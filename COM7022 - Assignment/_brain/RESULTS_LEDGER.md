# Results Ledger: COM7022 Product Clustering

Frozen from execution of `COM7022_Clustering_25199053.ipynb` (random seed 42) on 2026-10-24. Every figure, table and text claim in the report must match these exact numbers.

## 1. Dataset audit

- Raw rows: **1,000**, columns: **10**. Clean rows: **997** (3 rows dropped with no text and no sales/stock info).
- Full-row duplicates: **0**. Duplicate `details`: **39** (multiple sellers listing identical product descriptions).
- Raw missing values: `available` 111, `lastUpdated` 53, `sold` 8, `price` 5, `Catatory` 3, `text` 3, `Item_Name` 1, `priceWithCurrency` 1.
- Recovered from other fields of the same listing:
  - 5 missing prices recovered from `priceWithCurrency` (0 disagreements where both exist).
  - 3 Canadian-dollar prices converted at fixed 0.73 CAD/USD.
  - 2 missing units-sold recovered from `text` ("... / N sold"; 0 disagreements where both exist).
  - 3 listings with available stock but no "sold" substring set to `sold = 0`.
- Stock availability handling:
  - 299 listings with "More than 10 available" coded as **11** (the capped value).
  - 115 listings with explicit availability > 10 capped at 11 for consistency.
  - 47 listings with "Last One" coded as **1**.
  - 62 listings with "Limited quantity available" or lots imputed with median (**11**), flagged via `stock_imputed = 1`.
- Skewness reduction:
  - Price: raw skewness **2.18** -> `log(1 + price)` skewness **-0.08**.
  - Units sold: raw skewness **11.23** -> `log(1 + sold)` skewness **0.25**.

## 2. Selected features

Three features: `log_price`, `log_sold`, `stock_level`.
Spearman rank correlations:
- `log_price` vs `log_sold`: **-0.14**
- `log_price` vs `stock_level`: **-0.16**
- `log_sold` vs `stock_level`: **+0.37**

## 3. PCA (3 features, standardised)

- PC1: **48.6%** of variance (loadings: `log_price` -0.421, `log_sold` +0.636, `stock_level` +0.647). Measures volume/stock contrast with price.
- PC2: **30.1%** of variance (loadings: `log_price` +0.906, `log_sold` +0.335, `stock_level` +0.260). Measures pure price tier.
- PC1 + PC2 cumulative explained variance: **78.7%**.

## 4. Model comparison (frozen numbers)

| Metric | K-Means (k = 4) | Hierarchical (Ward, k = 4) | DBSCAN (eps = 0.45, min_samples = 6) |
|---|---:|---:|---:|
| Clusters found | **4** | **4** | **2** (+ noise) |
| Noise share (%) | **0.0%** | **0.0%** | **8.9%** (89 listings) |
| Silhouette score | **0.307** | **0.253** | **-0.014** (clustered points only) |
| Davies-Bouldin index (lower is better) | **1.015** | **1.257** | **1.172** |
| Calinski-Harabasz score | **503.3** | **402.9** | **3.5** |
| Resampling stability (ARI mean ± SD, 30 runs @ 80%) | **0.932 ± 0.025** | **0.481 ± 0.084** | **0.749 ± 0.063** |
| Smallest cluster share (%) | **22.0%** (219) | **16.8%** (167) | **0.4%** (4) |
| Largest cluster share (%) | **31.3%** (312) | **35.9%** (358) | **90.7%** (904) |

Agreement between K-Means and Ward: Adjusted Rand Index = **0.468**.

## 5. Sensitivity and robustness checks

- K-Means across 10 random seeds (mean pairwise ARI): **0.984** (min **0.936**).
- z-score scaling vs min-max scaling (ARI): **0.492** (weighting choice affects boundaries).
- With vs without top 1% volume outliers (ARI on remaining 987 rows): **0.937** (high-volume sellers do not distort the clustering on the log scale).

## 6. Final K-Means cluster profiles (k = 4, n = 997)

| Metric | Cluster 0 (Premium slow-moving) | Cluster 1 (Budget slow-moving) | Cluster 2 (Best-sellers) | Cluster 3 (Low-stock) |
|---|---:|---:|---:|---:|
| Listings (count, %) | 219 (22.0%) | 224 (22.5%) | 242 (24.3%) | 312 (31.3%) |
| Median price | **$68.99** | **$18.99** | **$29.94** | **$39.99** |
| Median units sold | **43** | **30** | **952** | **16** |
| Mean units sold | 131 | 61 | 2,934 | 54 |
| Share of all units sold | **3.7%** | **1.8%** | **92.3%** | **2.2%** |
| Median stock level | 11 (max) | 11 (max) | 11 (max) | **3** |
| Listings showing "Last One" (%) | 0.0% | 0.0% | 1.2% | **14.1%** |
| Ships from United States (%) | 84.9% | 92.0% | 99.6% | 88.5% |
| Median days since last update | 2.1 | 3.1 | 1.1 | 1.6 |
| Dominant product type | Eau de Parfum (45.2%) | Eau de Toilette (37.9%) | Eau de Toilette (67.8%) | Eau de Toilette (39.1%) |
| Top three brands | Giorgio Armani, Paco Rabanne, YSL | Unbranded, Lattafa, Ralph Lauren | Armaf, Ralph Lauren, Giorgio Armani | Giorgio Armani, Paco Rabanne, Ralph Lauren |
