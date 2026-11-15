<!-- Master source of the COM7022 report. Built into the Word/PDF report and the GitHub Pages portal
     by scripts/build_report.py. Every number is taken from output/ (notebook run).
     Directives: ::: part | ::: figure stem | caption | ::: shot stem | caption | ::: table key | ::: callout Title ... :::
     ::: kpis | ::: recs | ::: explorer | ::: appendix | $$latex$$ | [[key]] = cross-reference | <!-- count:x --> = word-count bucket -->

<!-- count:intro -->
# 1. Project Background {#introduction}

## 1.1 Commercial Context

This portfolio is written as a Machine Learning Analyst at a fast-growing multi-seller e-commerce marketplace. Independent merchants list competing offers for the same fragrances, so catalogue growth outpaces manual curation. Management needs a scalable, data-driven view to decide which listings to promote, replenish or retire.

## 1.2 Marketplace Data Overview

The analysis uses `Sales-[5444].csv`: **1,000 listings across 10 attributes** covering identity (`Item_Name`, `details`, `Catatory`), pricing (`price`, `priceWithCurrency`), availability and sales (`available`, `text`, `sold`), maintenance history (`lastUpdated`) and origin (`itemLocation`). The catalogue covers men's fragrances, led by US-based sellers (**912 of 1,000 raw listings; 909 of 997 cleaned**) alongside cross-border offers led by Hong Kong (52). Each row is a **seller listing rather than a unique product**: the same fragrance appears across multiple offers with different prices and stock levels, so segments describe commercial offers rather than brands.

## 1.3 Core Problem Formulation

Three barriers prevent manual catalogue management. First, **scale**: listing growth outpaces manual review. Second, **data quality**: prices and sales appear inside free text, category labels are fragmented, and stock above ten units is censored. Third, **no ground-truth labels**: no field identifies best-sellers, premium niche offers or inventory risks, ruling out supervised learning. The task is therefore unsupervised discovery: what commercial segments exist, and how should each be managed?

## 1.4 Key Investigation Goals

- **O1 — Data readiness:** audit, clean and transform the extract reproducibly.
- **O2 — Segmentation:** apply K-Means, Hierarchical (agglomerative) clustering, DBSCAN and HDBSCAN to group listings by characteristics and sales performance.
- **O3 — Rigorous evaluation:** compare models using complementary internal, stability and sensitivity metrics.
- **O4 — Model selection:** justify the technically strongest and operationally suitable model for e-commerce.
- **O5 — Business translation:** convert segments into evidence-based actions for executive stakeholders.

## 1.5 Analytical Framework

The investigation follows a structured lifecycle ([[fig15_workflow]]) implemented in a Python notebook (`pandas` and `scikit-learn`; McKinney, 2010; Pedregosa et al., 2011) with fixed random seed 274. Re-executing the notebook from a clean state reproduces every reported figure.

::: figure fig15_workflow | End-to-end methodological workflow, from business problem to recommended actions.

<!-- count:task1 -->
::: part Task 1 | Practical Machine Learning Investigation

# 2. Data Preparation {#data-preparation}

## 2.1 Data Quality Audit

A systematic audit preceded modelling. The raw extract holds **zero full-row duplicates**, though 34 listings share identical product descriptions across competing sellers. Eight columns contain missing values ([[table_missing]], [[fig01_missing_values]]), led by `available` (111 rows, 11.1%) and `lastUpdated` (53 rows, 5.3%).

Descriptive profiling revealed four structural issues that would distort distance-based clustering:

- **Extreme skew.** Units sold span 1 to 54,052 against a median of 49.5 (skewness 9.70), while price is also right-skewed (2.04); Euclidean distances on raw values would be dominated by viral outliers ([[fig02_raw_distributions]]).
- **Censored stock.** The marketplace displays "More than 10 available" for 299 listings and records them numerically as 10—a reporting ceiling rather than an exact count.
- **Label fragmentation.** `Catatory` holds 63 distinct strings caused by spelling and capitalisation variants of a few fragrance types.
- **Mixed currency.** 996 prices are quoted in US dollars (plus one unlabelled US listing), whereas three listings are quoted in Canadian dollars.

::: table table_missing
::: figure fig01_missing_values | Missing values by attribute in the raw extract.
::: figure fig02_raw_distributions | Raw distributions of price and units sold, showing the extreme right skew.

## 2.2 Cleaning Strategy

Preparation followed one rule: **recover before you impute**. Missing values were first reconstructed from companion fields in the same listing, and statistical imputation was applied only when understood and flagged ([[table_cleaning]], [[fig16_data_prep_flow]]).

::: figure fig16_data_prep_flow | Data preparation pipeline from the raw extract to model-ready features.

- **Price and sales recovery.** All five missing prices were restored from `priceWithCurrency`, which matched `price` exactly in all 994 rows holding both. The three Canadian-dollar prices were converted to US dollars at a documented rate (0.73 USD/CAD) so all listings share one currency. Two `sold` values were parsed from `text`, and three listings showing stock without a "sold" string were set to zero.
- **Stock reconstruction.** "More than 10" and explicit counts above ten were coded as 11 (*well stocked*), "Last One" as 1, and 62 unquantified "Limited quantity" or lot listings received the median with a `stock_imputed` indicator so their influence could be audited. Retaining that indicator prevents synthetic stock values from hiding real inventory fragility during post-hoc evaluation.
- **Category normalisation.** The 63 raw strings were grouped into six unified types: Cologne, Eau de Toilette, Eau de Parfum, concentrated Parfum, generic fragrance and Other.
- **Record retention.** Only three listings lacking both sales and stock information were dropped, leaving **997 verified listings**. High-volume outliers were deliberately retained because viral best-sellers represent genuine commercial concentration rather than measurement errors; trimming them would hide the marketplace's primary revenue engine.

::: table table_cleaning
::: shot code02_missing_values | Missing-value and duplicate audit.
::: shot code03_price_recovery | Recovery of price from priceWithCurrency and currency conversion.
::: shot code04_sold_recovery | Recovery of units sold from the listing text.
::: shot code05_stock_level | Stock reconstruction and treatment of censoring.
::: shot code06_product_type | Normalisation of 63 category labels into six product types.

## 2.3 Transformation, Scaling and Categorical Variables

**Logarithmic transformation.** A $\log(1 + x)$ transform was applied to price and units sold. It preserves zero values and rank order while compressing long right tails, reducing skewness from 1.97 to 0.09 for price and from 9.72 to 0.52 for units sold ([[table_clean_desc]], [[fig03_transformed_distributions]]).

**Standardisation.** Because all clustering methods here measure Euclidean distance, each feature was z-score standardised so every input contributes equal variance (Müller and Guido, 2016):

$$z = \frac{x - \mu}{\sigma}$$

Min-max normalisation was tested and rejected: it over-weights the bounded 1–11 stock scale relative to log distributions and materially changes cluster boundaries (ARI 0.49; Section 4.6).

**Categorical variables.** Brand (246 values), product type and country were excluded from distance calculation. One-hot encoding would create hundreds of sparse dimensions allowing individual brands to dominate the geometry; these attributes were reserved for post-hoc profiling.

::: table table_clean_desc
::: figure fig03_transformed_distributions | Feature distributions after the logarithmic transformation.
::: shot code07_log_transform | Logarithmic transformation of skewed measures.
::: shot code08_scaling | Z-score standardisation of the selected features.

## 2.4 Feature Selection

Candidate features were screened via Spearman rank correlation ([[fig04_feature_correlation]]) and a systematic scan of five feature subsets ([[table_featuresets]]). Correlations are weak to moderate (price–sales −0.13, price–stock −0.20, sales–stock +0.35), confirming low collinearity across distinct commercial mechanisms.

**Set B**—**log price, log units sold and stock level**—was selected to represent market positioning, demand and supply risk. A two-feature baseline (Set A) scores slightly higher silhouette but omits inventory availability. Adding listing recency or bottle size lowered separation without adding actionable insight: half of bottles fall between 3.3 and 3.7 oz, and three-quarters of listings were updated within a week.

::: table table_featuresets
::: figure fig04_feature_correlation | Spearman rank correlation between candidate features.

# 3. Model Selection {#model-selection}

## 3.1 Clustering in Brief

Unsupervised clustering groups unlabelled observations by geometric proximity in feature space, uncovering natural commercial profiles rather than predicting a target variable (Müller and Guido, 2016).

## 3.2 Candidate Techniques

Four techniques were chosen to span contrasting definitions of a cluster ([[table_techniques]]):

- **K-Means** (MacQueen, 1967) partitions listings into $k$ compact clusters by iteratively updating centroids to minimise within-cluster sum of squares:

$$J = \sum_{j=1}^{k} \sum_{x_i \in C_j} \lVert x_i - \mu_j \rVert^2$$

- **Agglomerative hierarchical clustering** builds a bottom-up dendrogram from singleton leaves. Under **Ward linkage** (Ward, 1963), each merge minimises the incremental increase in within-group variance ($SS_{within}$).
- **DBSCAN** (Ester et al., 1996) discovers density-connected regions requiring at least `min_samples` neighbours within radius $\varepsilon$, isolating sparse points as noise so outliers cannot pull centroids.
- **HDBSCAN** (Campello et al., 2013; McInnes et al., 2017) removes DBSCAN's fixed-$\varepsilon$ constraint via mutual reachability distance, extracting the most persistent clusters across varying densities.

::: table table_techniques

## 3.3 Projecting the Features with PCA

With only three inputs, Principal Component Analysis (Pearson, 1901) served for 2D projection rather than noise reduction. Two components retain **78.7%** of variance ([[fig05_pca_variance_biplot]], [[table_pca]]): **PC1 (48.6%)** loads positively on sales (+0.636) and stock (+0.647) against price (−0.421), capturing *commercial traction*, while **PC2 (30.1%)** is dominated by price (+0.906), capturing *price tier*. Clustering itself remained in the full three-dimensional standardised space so the remaining 21.3% of variance (primarily orthogonal differences between price and stock) stays intact during distance calculations, while plotting onto PC1 and PC2 visually preserves the main commercial structure.

::: table table_pca
::: figure fig05_pca_variance_biplot | Explained variance (left) and loading biplot (right) of the principal components.

# 4. Model Implementation and Evaluation {#evaluation}

## 4.1 K-Means

K-Means was evaluated across $k = 2\text{–}10$ with k-means++ initialisation, 20 restarts and seed 274 ([[table_kscan]], [[fig06_kmeans_elbow_silhouette]]). Inertia drops 38.9% from $k = 2$ to $k = 4$ before flattening into an elbow, indicating diminishing compacting gains beyond four groups. Although $k = 2$ maximises silhouette (0.337), a binary split merely separates fast from slow movers and hides pricing and inventory differences needed for catalogue action. **$k = 4$** achieves a near-minimal Davies-Bouldin index (1.013; only $k = 10$ is slightly lower at 1.004 with clusters down to 71 items), solid silhouette (0.307) and balanced sizes (22–31% of listings). All four clusters show positive mean silhouettes (0.29–0.32), with only 1.2% negative points indicating mild boundary overlap ([[fig07_kmeans_clusters_silhouette]]).

::: table table_kscan
::: figure fig06_kmeans_elbow_silhouette | Elbow (inertia) and silhouette criteria across k.
::: figure fig07_kmeans_clusters_silhouette | K-Means (k = 4) on the PCA plane and per-cluster silhouette profile.

## 4.2 Hierarchical Clustering

Four linkage criteria were tested on identical Euclidean distances ([[table_linkage]]). Single and average linkage suffer from *chaining*, absorbing almost every listing into one group (994 and 989), while complete linkage produces uneven fragments (424/388/180/5). **Ward linkage** creates balanced clusters (358/237/235/167) and the highest linkage silhouette (0.253), cutting cleanly into four branches around merge height 21 ([[fig09_ward_dendrogram_cut]]) for direct comparison with K-Means (ARI 0.41).

$$\Delta(A,B) = \frac{n_A\, n_B}{n_A + n_B} \lVert \mu_A - \mu_B \rVert^2$$

::: table table_linkage
::: figure fig09_ward_dendrogram_cut | Ward dendrogram with the four-cluster cut.

## 4.3 DBSCAN

Setting `MinPts` = 6 ($2 \times d$), the sorted 6-nearest-neighbour distance plot rises smoothly with no sharp knee ([[fig10_dbscan_k_distance]]), indicating no separated density islands. Across a 32-setting grid ($\varepsilon \in [0.25, 0.70]$, `min_samples` $\in \{4, 6, 10, 15\}$), $\varepsilon \le 0.35$ rejects 13–89% as noise while larger radii collapse almost everything together. The best trade-off (**$\varepsilon = 0.45$**) puts 904 listings (90.7%) into one cluster, 4 into a second and 89 (8.9%) into noise (silhouette −0.014; [[fig11_dbscan_clusters]]). This informative negative result confirms a **continuum**, while making DBSCAN useful for flagging anomalies (noise medians: $26 vs $36 price, 163 vs 46 sold, 5 vs 9 stock).

::: figure fig10_dbscan_k_distance | Sorted 6-nearest-neighbour distances used to select ε.
::: figure fig11_dbscan_clusters | DBSCAN partition on the PCA plane; grey points are noise.

## 4.4 HDBSCAN

HDBSCAN (`MinPts` = 6) tested whether DBSCAN failed solely due to a single global $\varepsilon$. Across a 15-configuration grid, every `min_cluster_size` from 20 to 100 yielded the identical partition: **two clusters and 47.0% noise** ([[table_hdbscan]], [[fig18_hdbscan]]). The larger cluster reflects the censoring artefact (89.1% at the stock ceiling vs 41.5% overall); the smaller is a low-stock group (median 3). Jittering the integer stock scale or dropping stock still leaves 40–50% unassigned, confirming the continuum and exposing a data-quality issue.

::: table table_hdbscan
::: figure fig18_hdbscan | HDBSCAN on the PCA plane (a) and its alignment with the censored stock ceiling (b).

## 4.5 Evaluation Framework

Without ground-truth target labels, clustering quality cannot rely on supervised accuracy and was triangulated across cohesion, separation and stability ([[table_metrics]]). Point-level silhouette width $s(i)$ (Rousseeuw, 1987) compares intra-cluster distance $a(i)$ against nearest-neighbour distance $b(i)$:

$$s(i) = \frac{b(i) - a(i)}{\max\{a(i),\, b(i)\}}$$

Global compactness and separation were quantified via Davies-Bouldin (Davies and Bouldin, 1979) and the Calinski-Harabasz variance ratio (Caliński and Harabasz, 1974), while reproducibility across 30 bootstrap resamples (80% subsamples) and sensitivity checks was measured with the Adjusted Rand Index (Hubert and Arabie, 1985).

::: table table_metrics

## 4.6 Comparative Results

::: table table_comparison
::: figure fig12_model_comparison | Internal validity and stability by model; hatched bars are scored on clustered listings only.

Among full-coverage models, K-Means leads on **every internal metric**: silhouette 0.307 vs 0.253 (Ward), Davies-Bouldin 1.013 vs 1.257, and Calinski-Harabasz 503.3 vs 402.9. HDBSCAN's 0.480 silhouette is not comparable because it scores only the 53% of retained listings and discards ambiguous borderline offers. Resampling stability is decisive: K-Means reaches **ARI 0.929 ± 0.033** because iterative centroid updates realign smoothly across subsamples, whereas Ward drops to **0.480 ± 0.063** as greedy, irreversible early merges amplify small sampling perturbations up the hierarchy. Sensitivity checks confirm robustness ([[table_sensitivity]]): changing seed (ARI 0.964) or removing the top 1% of sellers (0.943) barely shifts partitions, whereas min-max scaling (0.494) distorts feature weighting.

::: table table_sensitivity
::: callout Model Selection Decision
**K-Means (k = 4)** is selected as the production engine for its top internal validity, high stability and full coverage. Ward serves as a structural cross-check, DBSCAN as an anomaly flag and HDBSCAN as a data-quality probe.
:::

# 5. Cluster Characteristics {#clusters}

Mapping centroids to business units reveals four commercial segments ([[table_profiles]], [[fig13_cluster_profiles]], [[fig14_cluster_distributions]]):

- **Cluster 2 — Best-Sellers (24.3%):** Generate **90.7% of all units sold** (697,569 of 769,317) at median $29.76 with full stock; largely Eau de Toilette (Armaf, Ralph Lauren), anchoring core marketplace throughput.
- **Cluster 0 — Premium Designer (22.7%):** Highest prices (median $67.14) with steady, slower volume (3.8%); dominated by Eau de Parfum (Giorgio Armani, Paco Rabanne, Yves Saint Laurent), where brand equity supports stronger margins.
- **Cluster 1 — Budget Commodities (21.7%):** Cheapest offers (median $18.10) yet only 1.7% of sales, containing the highest share of unbranded listings—demonstrating that discounting alone cannot substitute for brand demand.
- **Cluster 3 — Low-Stock Tail (31.4%):** Median stock 3, 14.7% at "Last One" and low sales (3.8%, median 16), signalling imminent stock-out risk or stale, uncompetitive inventory.

::: table table_profiles
::: explorer
::: figure fig13_cluster_profiles | Standardised feature means per cluster.
::: figure fig14_cluster_distributions | Price, sales and stock distributions within each cluster.

<!-- count:task2 -->
::: part Task 2 | Critical Report for Executive Stakeholders

# 6. Executive Summary {#executive-summary}

Our 997 fragrance listings divide into **four commercially distinct segments**. Just one quarter—the best-sellers—drives **91% of all units sold**, while nearly a third sit close to stock-out. **K-Means (four segments)** outperformed three alternatives on internal validity and stability, covers every listing, and scores new inventory automatically. Each group warrants a distinct strategy: *protect, grow, reposition* or *audit*. Because clustering reveals association rather than causation, each action is framed as a controlled test with an explicit stop rule (Section 7.6).

::: kpis

# 7. Critical Evaluation {#critical-evaluation}

## 7.1 Suitability of Methods and Design Decisions

Unsupervised clustering suits an unlabelled catalogue where discovery precedes prediction. Three design choices drove success: log-transforming price and sales prevented viral listings from dominating Euclidean distances; selecting price, sales and stock aligned geometry with core commercial questions (*value, demand, stock risk*); and excluding brand and country prevented brand-only silos. Sensitivity checks verified that these partitions hold across random seeds and top-seller removal.

## 7.2 Cluster Count is a Business Decision, Not a Discovery

Diagnostic metrics disagree rather than identifying one natural optimum. Silhouette (0.337) and Calinski-Harabasz (536.7) peak at a trivial $k = 2$ cut, whereas Davies-Bouldin reaches its minimum at a fragmented $k = 10$ (1.004). Density methods find no natural gaps: DBSCAN merges 91% into one cluster and HDBSCAN leaves 47% unassigned. Even K-Means shifts slightly across seeds (ARI 0.96). Together, this shows the catalogue forms a **continuous market spectrum** without discrete natural islands. Consequently, $k = 4$ is chosen operationally to match four distinct commercial actions, treating boundaries as soft guidelines.

## 7.3 Value Beyond a Simple Sales Ranking

Demand is heavily concentrated: the top quartile delivers 94% of sales. A simple threshold (`sold >= 300`) already captures 87% of best-sellers at 83% precision, so clustering adds modest value at the top. Its real contribution lies in splitting the remaining 75% by price and stock. A shallow depth-3 decision tree (eight rules) reproduces all four segments with ~90% cross-validated accuracy ([[table_rules]]), splitting first on stock, then sales, then price. Operations can deploy these transparent rules directly while refreshing K-Means monthly to recalibrate thresholds.

::: table table_rules

## 7.4 Measurement Artefacts Versus Market Structure

The platform caps visible stock at "More than 10 available" (coded 11), placing 41.5% of listings on an artificial ceiling. HDBSCAN was drawn directly to this artefact, with 89% of its primary cluster sitting at 11. Inside K-Means, only the **Low-Stock Tail** (0% at ceiling) reflects exact inventory counts; the remaining three segments sit 54–64% on the ceiling, so their separation relies primarily on price and sales. "Last One" alerts are therefore trustworthy, whereas "deep stock" claims remain unverified—making exact stock counts our highest-value data upgrade.

## 7.5 Fair Model Comparison and Operational Fit

Headline scores can mislead. HDBSCAN's 0.480 silhouette reflects selection bias from scoring only the 53% easiest points, while DBSCAN's 0.749 stability merely reflects a degenerate 91% single cluster. Conversely, Ward's low stability (0.480) exposes how sensitive greedy hierarchical merges are to sampling noise. For production e-commerce ([[table_ecom]]), only **K-Means** satisfies all five operational needs: full coverage, instant scoring, refresh stability, linear scaling and clear business interpretation.

::: table table_ecom

## 7.6 Commercial Value and Testable Hypotheses

Unit volume understates the premium tier. Weighting sales by price as a rough revenue proxy, best-sellers drive 83.2% and budget offers just 0.8%, whereas **Premium Designer captures 9.5% from 3.8% of units**—2.5× its unit share. An average best-seller listing is worth roughly 90× an average budget listing on this indicative measure (listed price × cumulative units sold, not accounting revenue).

Because price–sales correlation is weak (−0.13), Section 8 actions are framed as **testable hypotheses** with clear stop rules rather than guaranteed causal levers. For instance, paid promotion on budget items should be paused on a random 50% test group for four weeks, retaining spend only where incremental sales cover ad cost, while Premium Designer listings should prioritise brand-story merchandising and selective bundling rather than margin-eroding discounts. Our strategy would change if exact stock separated overstocked items from healthy stock, if monthly refreshes showed rapid migration across segments (making segments temporary states rather than product types), or if controlled budget tests proved profitable.

# 8. Recommendations for Business Managers {#recommendations}

The four segments translate into targeted, measurable interventions ([[fig17_segment_actions]]):

::: figure fig17_segment_actions | Share of listings versus share of units sold per segment, with the recommended action.
::: recs

Execution should prioritise **Cluster 2** (protecting core volume) and **Cluster 3** (inventory cleanup), piloting each intervention first (Section 7.6). Success should be tracked via Cluster 2 stock-out rates, 30-day Cluster 3 restock/delist ratios, Cluster 0 attachment or bundle conversion, and net sales per advertising dollar in Cluster 1. Governance should refresh K-Means monthly with fixed centroid tracking, score new listings automatically on arrival, and route DBSCAN noise points to buyers or pricing managers as priority anomalies requiring manual validation.

# 9. Limitations {#limitations}

This single-category snapshot captures listings updated mainly around April–May 2024 and may not generalise across seasonal peaks, gifting cycles or other product lines. Stock censoring limits visibility into genuine overstocking above ten units (Section 7.4), and our revenue proxy ignores seller fees, shipping costs and product margins. Above all, clustering establishes commercial association rather than causal elasticity, so borderline listings near cluster edges require buyer review alongside automated rules.

# 10. Conclusion and Future Work {#conclusion}

Careful preparation transformed a messy, unlabelled catalogue into four actionable segments, exposing extreme demand concentration. Three lessons stand out: **preparation outweighed algorithm tuning**, **segment count is an executive decision on a continuum**, and **density methods added diagnostic value** despite failing as segmenters. Future work should integrate accounting margins, exact stock levels and description embeddings, track monthly segment migration, and deploy a lightweight manager dashboard.

<!-- count:none -->
# References {#references}

- Campello, R.J.G.B., Moulavi, D. and Sander, J. (2013) 'Density-based clustering based on hierarchical density estimates', in *Advances in Knowledge Discovery and Data Mining (PAKDD 2013)*. Berlin: Springer, pp. 160–172.
- Caliński, T. and Harabasz, J. (1974) 'A dendrite method for cluster analysis', *Communications in Statistics*, 3(1), pp. 1–27.
- Davies, D.L. and Bouldin, D.W. (1979) 'A cluster separation measure', *IEEE Transactions on Pattern Analysis and Machine Intelligence*, PAMI-1(2), pp. 224–227.
- Ester, M., Kriegel, H.-P., Sander, J. and Xu, X. (1996) 'A density-based algorithm for discovering clusters in large spatial databases with noise', in *Proceedings of the Second International Conference on Knowledge Discovery and Data Mining*. Portland: AAAI Press, pp. 226–231.
- Hubert, L. and Arabie, P. (1985) 'Comparing partitions', *Journal of Classification*, 2(1), pp. 193–218.
- MacQueen, J. (1967) 'Some methods for classification and analysis of multivariate observations', in *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability*. Berkeley: University of California Press, pp. 281–297.
- McInnes, L., Healy, J. and Astels, S. (2017) 'hdbscan: Hierarchical density based clustering', *Journal of Open Source Software*, 2(11), p. 205.
- McKinney, W. (2010) 'Data structures for statistical computing in Python', in *Proceedings of the 9th Python in Science Conference*, pp. 56–61.
- Müller, A.C. and Guido, S. (2016) *Introduction to Machine Learning with Python*. Sebastopol: O'Reilly Media.
- Pearson, K. (1901) 'On lines and planes of closest fit to systems of points in space', *Philosophical Magazine*, 2(11), pp. 559–572.
- Pedregosa, F. et al. (2011) 'Scikit-learn: machine learning in Python', *Journal of Machine Learning Research*, 12, pp. 2825–2830.
- Rousseeuw, P.J. (1987) 'Silhouettes: a graphical aid to the interpretation and validation of cluster analysis', *Journal of Computational and Applied Mathematics*, 20, pp. 53–65.
- Ward, J.H. (1963) 'Hierarchical grouping to optimize an objective function', *Journal of the American Statistical Association*, 58(301), pp. 236–244.

# Appendix A: Reproducible Code {#appendix}

The complete Task 1 implementation is a single Jupyter notebook executing end to end in under 10 seconds locally with fixed random seed 274. All materials—notebook, dataset, figures, tables and code screenshots—are hosted in the repository: https://github.com/kvmmn/_COM7022_MachineLearning. The full notebook code follows, one screenshot per cell in execution order.

::: appendix

**AI use declaration.** AI tools were used to support structuring and proofreading. All analysis was executed, verified and interpreted by the author, and every reported figure was checked against the notebook output.
