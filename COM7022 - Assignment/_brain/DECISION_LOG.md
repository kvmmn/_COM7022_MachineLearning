# Decision Log: COM7022 Product Clustering

## D01: Unit of observation
- **Choice:** Each row is one product listing, not an aggregated brand or a customer.
- **Evidence:** `Sales-[5444].csv` contains 1,000 marketplace offers, where multiple sellers list the same perfume with different prices, stocks, and sales counts.
- **Alternative considered:** Grouping by brand (`Item_Name`). Rejected because the business question asks to segment "products based on their characteristics and sales performance", and the variation in price and stock happens between listings of the same brand.

## D02: Missing price recovery before imputation
- **Choice:** Recover all 5 missing `price` values from `priceWithCurrency`.
- **Evidence:** For all 995 listings where both columns are present, the extracted numeric price matches `price` exactly (0 disagreements > $0.01).
- **Alternative considered:** Mean or median imputation. Rejected because exact true values are already present in the raw text.

## D03: Canadian dollar conversion
- **Choice:** Convert 3 Canadian-dollar listings at a documented rate of 0.73 USD/CAD.
- **Evidence:** `priceWithCurrency` shows `C $` for rows 352, 379, 957, all located in Ontario, Canada.
- **Alternative considered:** Dropping the rows or ignoring currency. Dropping loses valid products; ignoring distorts price by ~37%.

## D04: Missing units-sold recovery
- **Choice:** Recover 2 missing values from `text` ("... / N sold"); set 3 rows with stock but no "sold" substring to `sold = 0`; drop 3 rows that contain no text and no sales/stock info.
- **Evidence:** Where both `sold` and `text` exist, they agree perfectly. Rows with no text carry zero information on sales performance.

## D05: Stock availability reconstruction and capping
- **Choice:** Code "More than 10 available" as 11; cap all explicit availability numbers > 10 at 11; code "Last One" as 1; median-impute unquantified "Limited quantity" / lot listings (62 rows) and flag them with `stock_imputed = 1`.
- **Evidence:** 299 listings have censored availability ("More than 10"). Without capping, an uncensored listing showing 100 available would look 10x larger than a censored listing with 100+ available. Capping at 11 creates a uniform scale where 11 means "well stocked".
- **Alternative considered:** Dropping censored rows. Rejected because 30% of the dataset would be lost.

## D06: Category normalisation
- **Choice:** Collapse ~50 messy category labels into 6 standard fragrance types (`Eau de Toilette`, `Eau de Parfum`, `Cologne`, `Parfum / Extrait`, `Generic fragrance`, `Other`).
- **Evidence:** Many labels are typos or capitalisation variants (`Eau De Parfum`, `eau de perfume`, `eau de toillette`).

## D07: Logarithmic transformation of price and sales
- **Choice:** Apply `log(1 + x)` to both `price` and `sold`.
- **Evidence:** Skewness after cleaning is 1.97 for price and 9.72 for units sold (max sold = 54,052 vs median = 49.5). After log transform, skewness falls to 0.09 and 0.52 respectively, creating near-symmetric distributions where Euclidean distances are meaningful.
- **Alternative considered:** Dropping high-volume sellers as outliers. Rejected because top-selling products are commercially critical. Log transformation retains them without letting them distort distance calculations.

## D08: Feature selection (Set B)
- **Choice:** Select three features: `log_price`, `log_sold`, and `stock_level`.
- **Evidence:** Set B balances technical cluster quality (silhouette ~0.31, Davies-Bouldin ~1.01) with the three required business dimensions: market position (price), sales traction (sold), and inventory risk (stock). Adding `days_since_update` or `size_oz` drops silhouette to 0.25-0.27 without adding actionable separation.
- **Categorical features:** Kept for post-hoc profiling rather than distance computation to avoid one-hot distortion.

## D09: Scaling choice
- **Choice:** Standardisation (z-scores: mean 0, standard deviation 1).
- **Evidence:** All three algorithms use Euclidean distance. Standardisation ensures each feature contributes equal initial variance. Min-max scaling was evaluated in sensitivity testing (ARI = 0.492) and rejected because it over-weights bounded features relative to log distributions.

## D10: Choice of k = 4 for K-Means
- **Choice:** 4 clusters.
- **Evidence:** Inertia elbow between k = 3 and k = 5; Davies-Bouldin index reaches its minimum across all k at k = 4 (1.015); silhouette remains solid (0.307); cluster sizes are well balanced (22% to 31%), mapping cleanly to four distinct commercial roles (Best-sellers, Premium slow-movers, Budget slow-movers, Low-stock).

## D11: Final model selection
- **Choice:** K-Means selected as primary model.
- **Evidence:** Superior internal validation (silhouette 0.307 vs Ward 0.253; DBI 1.015 vs 1.257); exceptional resampling stability (ARI 0.932 vs Ward 0.481); full partition with 0% noise (unlike DBSCAN's 8.9% noise and 91% single cluster); linear inference for scoring incoming listings.
- **Role for other models:** Ward used as a hierarchical cross-check (ARI = 0.411); DBSCAN used as an operational outlier detector.

## D12: HDBSCAN as a fourth technique (2026-10-27)
- **Choice:** HDBSCAN (scikit-learn 1.3+) with min_samples = 6 (same as DBSCAN) and min_cluster_size = 30 (about 3% of listings, the smallest group worth its own action).
- **Evidence:** With min_samples = 6, every min_cluster_size from 20 to 100 gives the same result: 2 clusters, 47.0% noise. The larger cluster is 89.1% listings at the censored stock ceiling (41.5% of all listings sit at 11); the smaller is a low-stock group (median 3). Jittering stock by ±0.5 or dropping stock still leaves about 40-50% noise.
- **Reading:** Silhouette 0.480 and DBI 0.785 are computed on the 53% of listings kept, so they are not comparable with full-coverage models (hatched in Figure 12). HDBSCAN confirms the continuum and exposes a data-quality effect; it is kept as a data-quality probe, not a segmentation.

## D13: Print-first visual system (2026-10-27)
- **Choice:** All figures, diagrams and code screenshots are drawn at final printed size (6.6 in text width, or 4.6 in narrow) at 300 dpi, in Carlito (metric-compatible with the report's Calibri), with fixed type sizes (8.5 pt labels, 7.5 pt ticks, 9 pt panel titles) and one colour per segment (0 steel blue, 1 ochre, 2 tiffany, 3 terracotta). The Word report inserts each image at native size, so type is identical across figures. The PDF is the primary deliverable; the HTML portal is secondary.

## D14: TabClustPFN as a state-of-the-art benchmark (2026-10-27)
- **Choice:** TabClustPFN (Zhao et al., 2026; arXiv:2601.21656), the authors' public code and checkpoint, run twice on the same standardised features: automatic k and k = 4. R's `rpy2` is only used to generate pre-training data, so an import-time placeholder (raises if called) replaces it; licence CC BY-NC 4.0 (non-commercial coursework).
- **Evidence:** Automatic k = 2 (thin stock vs the rest), the same k on 30/30 subsamples, identical labels under row shuffling, stability ARI 0.966; 310 of 312 K-Means low-stock listings fall in its smaller cluster. At k = 4: silhouette 0.152, DBI 1.71 (K-Means 0.307, 1.015), stability 0.933, one group 97% at the stock ceiling.
- **Reading:** An independent pre-trained check that confirms the dominant stock structure and supports a small k; it does not beat K-Means for a four-way business segmentation. Kept as a check on k.

## D15: Colab run verified (2026-10-27)
- **What:** The notebook was executed on Google Colab (pandas 2.2.3, scikit-learn 1.6.1, CPU runtime) and saved to GitHub by Colab (commit 8acdcc8, with all outputs). Its code is identical to ours; the only added cell is Colab's "Open in Colab" badge.
- **Evidence:** Every metric in the model comparison, the sensitivity checks, the PCA variance, the Ward and DBSCAN cluster sizes, the HDBSCAN profile and the TabClustPFN results (auto k = 2, same k on 30/30 subsamples, row-shuffle ARI 1.0) match the local run. Only differences: HDBSCAN stability SD 0.149 (Colab) vs 0.147 (local), and TabClustPFN inference 43.8 s (Colab CPU) vs 3.2 s (local).
- **Consequence:** The notebook on main is now the executed Colab copy. `scripts/01_build_notebook.py` writes a notebook without outputs and would overwrite it, so it now includes the Colab badge cell and warns about this. `scripts/03_build_report_assets.py` finds cells by their first line, so extra cells cannot shift the code screenshots.
- **Open point:** Colab saved only the notebook. Figures and tables written to Colab's `output/` folder are not in the repo; the repo's `output/` files come from the local run. The inline Colab figures use the same style code but fall back to DejaVu Sans because Carlito is not installed on Colab.
