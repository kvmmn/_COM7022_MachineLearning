<!-- Master source of the COM7022 report. Built into the Word/PDF report (scripts/04_build_report_docx.py)
     and the GitHub Pages portal (scripts/02_build_review_html.py). Every number is taken from output/ (notebook run).
     Directives: ::: part | ::: figure stem | caption | ::: shot stem | caption | ::: table key | ::: callout Title ... :::
     ::: kpis | ::: recs | ::: explorer | ::: appendix | $$latex$$ | [[key]] = cross-reference | <!-- count:x --> = word-count bucket -->

<!-- count:intro -->
# 1. Introduction {#introduction}

## 1.1 Business Context

This portfolio is written from the position of a newly appointed Machine Learning Analyst at a rapidly growing e-commerce marketplace. The platform operates a multi-seller model: independent merchants list competing offers for the same products, so the catalogue expands far faster than any merchandising team can curate by hand. Commercial decisions that once relied on manual review (which listings to promote, which to replenish, which to retire) now require a scalable, data-driven view of the catalogue.

## 1.2 The Dataset

The analysis uses the company extract `Sales-[5444].csv`: **1,000 listings described by 10 attributes** covering product identity (`Item_Name`, `details`, `Catatory`), pricing (`price`, `priceWithCurrency`), availability and traction (`available`, `text`, `sold`), maintenance history (`lastUpdated`) and dispatch origin (`itemLocation`). The catalogue is a men's fragrance category, dominated by US-based sellers (909 listings) with a smaller cross-border segment led by Hong Kong (52). Critically, each row is a **seller listing rather than a unique product**: the same fragrance can appear several times at different prices and stock positions, so the resulting segments describe commercial offers, not manufacturers.

## 1.3 Problem Statement

Three obstacles prevent the company from managing this catalogue strategically. First, **scale**: manual review cannot keep pace with listing growth. Second, **data quality**: prices and sales are partly stored as free text, category labels are inconsistent and the platform censors stock above ten units. Third, **the absence of labels**: no field states whether a listing is a best-seller, a premium niche item or an inventory risk, which rules out supervised learning. The business question is therefore one of *discovery*: what natural commercial groups exist in the catalogue, and how should each be managed?

## 1.4 Project Objectives

- **O1 — Data readiness:** audit, clean and transform the dataset with every intervention evidenced and reproducible.
- **O2 — Segmentation:** apply K-Means, Hierarchical (agglomerative) clustering and DBSCAN to group listings by product characteristics and sales performance.
- **O3 — Rigorous evaluation:** compare models with complementary internal, stability and sensitivity measures rather than a single score.
- **O4 — Model justification:** select the model that is technically strongest *and* operationally suited to e-commerce.
- **O5 — Business translation:** convert segments into evidence-based actions for non-technical decision-makers.

## 1.5 Methodological Approach

The investigation follows a structured machine learning lifecycle ([[fig15_workflow]]). Each stage is implemented in a single Google Colab notebook with fixed random seeds, and every analytical decision is logged so that results can be regenerated end to end. The notebook was re-executed from a clean state before this report was written and reproduced every reported figure.

::: figure fig15_workflow | End-to-end methodological workflow, from business problem to recommended actions.

<!-- count:task1 -->
::: part Task 1 | Practical Machine Learning Investigation

# 2. Data Preparation {#data-preparation}

## 2.1 Data Quality Audit

A systematic audit preceded any modelling. The file contains **no full-row duplicates**, although 34 listings repeat an identical description, consistent with multi-seller offers rather than data-entry error. Missing values affect eight columns ([[table_missing]], [[fig01_missing_values]]); the largest gaps are in `available` (111 rows, 11.1%) and `lastUpdated` (53 rows, 5.3%).

Descriptive profiling exposed four structural problems that would distort any distance-based algorithm:

- **Extreme skew.** Units sold range from 1 to 54,052 against a median of 49.5 (skewness 9.70); price is also right-skewed (2.04). Euclidean distances on raw values would be dominated by a handful of viral listings ([[fig02_raw_distributions]]).
- **Censored stock.** The platform displays "More than 10 available" for 299 listings and stores the value as 10, so recorded stock is a ceiling, not a measurement.
- **Label fragmentation.** `Catatory` holds 63 distinct strings that are largely spelling and capitalisation variants of a few fragrance types.
- **Mixed currency.** Three prices are quoted in Canadian dollars.

::: table table_missing
::: figure fig01_missing_values | Missing values by attribute in the raw extract.
::: figure fig02_raw_distributions | Raw distributions of price and units sold, showing the extreme right skew.

## 2.2 Cleaning Strategy

Preparation followed a single principle: **recover before you impute**. Where a value was absent, it was first reconstructed from another field of the same listing; statistical imputation was used only where the cause of the gap was understood, and it was always flagged. Every step was recorded in an execution log ([[table_cleaning]]) and the overall flow is summarised in [[fig16_data_prep_flow]].

::: figure fig16_data_prep_flow | Data preparation pipeline from the raw extract to model-ready features.

- **Price and sales recovery.** All five missing prices were restored from `priceWithCurrency`, which matched the numeric field exactly across all 994 rows holding both. Two missing sales figures were parsed from the `text` field, and three listings showing stock but no sales were set to zero. Canadian prices were converted at a documented fixed rate.
- **Stock reconstruction.** Availability was rebuilt from listing wording: "More than 10" and any explicit value above ten were coded as 11 (*well stocked*), "Last One" as 1, and the 62 "Limited quantity" or lot listings received the median with an indicator column, so their influence could be audited.
- **Category normalisation.** The 63 raw labels were consolidated into six coherent product types (Eau de Toilette, Eau de Parfum, Cologne, Parfum/Extrait, Generic fragrance, Other).
- **Record retention.** Only three listings with neither sales nor stock information were removed, leaving **997 verified listings**. No commercially extreme listing was discarded, because best-sellers are precisely the observations the business must understand.

::: table table_cleaning
::: shot code02_missing_values | Missing-value and duplicate audit.
::: shot code03_price_recovery | Recovery of price from priceWithCurrency and currency conversion.
::: shot code04_sold_recovery | Recovery of units sold from the listing text.
::: shot code05_stock_level | Stock reconstruction and treatment of censoring.
::: shot code06_product_type | Normalisation of 63 category labels into six product types.

## 2.3 Transformation, Scaling and Categorical Variables

**Logarithmic transformation.** A log(1 + x) transform was applied to price and units sold. It preserves zero values and rank order while compressing the long right tail, reducing the skewness of units sold from 9.72 to 0.52 and of price from 1.97 to 0.09 ([[table_clean_desc]], [[fig03_transformed_distributions]]).

**Standardisation.** Because all three algorithms rely on Euclidean distance, each feature was converted to a z-score so that it contributes equal variance:

$$z = \frac{x - \mu}{\sigma}$$

Min-max normalisation was evaluated as an alternative and rejected: it inflates the bounded 1–11 stock scale relative to the log-transformed measures and changed the partition substantially (ARI 0.49; Section 4.5).

**Categorical variables.** Brand (246 values), product type and country were deliberately excluded from the distance computation. One-hot encoding would add hundreds of sparse dimensions and allow single brands to dominate the geometry; these attributes were instead reserved for post-hoc cluster profiling.

::: table table_clean_desc
::: figure fig03_transformed_distributions | Feature distributions after the logarithmic transformation.
::: shot code07_log_transform | Logarithmic transformation of skewed measures.
::: shot code08_scaling | Z-score standardisation of the selected features.

## 2.4 Feature Selection

Candidate features were screened with Spearman rank correlation ([[fig04_feature_correlation]]) and a systematic comparison of five feature sets ([[table_featuresets]]). The correlations are weak to moderate (price–sales −0.13, price–stock −0.20, sales–stock +0.35), confirming that each candidate captures a distinct commercial mechanism without problematic collinearity.

The final set comprises **log price, log units sold and stock level** (Set B), representing market position, demand and supply resilience. A two-feature baseline (Set A) achieves a marginally higher silhouette but ignores availability, which is central to the brief and to stock-out risk. Adding listing recency or bottle size reduced separation without adding actionable meaning: half of all bottles fall between 3.3 and 3.7 oz, and three-quarters of listings were updated within the past week.

::: table table_featuresets
::: figure fig04_feature_correlation | Spearman rank correlation between candidate features.

# 3. Model Selection {#model-selection}

## 3.1 Clustering in Brief

Clustering is an **unsupervised learning** task: it partitions observations so that members of a group are more similar to one another than to members of other groups, without reference to known outcomes. It is the appropriate paradigm here because the catalogue carries no commercial labels; the objective is to reveal structure, not to predict a target.

## 3.2 Candidate Techniques

Three algorithmic families were selected because they embody different definitions of a "cluster" ([[table_techniques]]):

- **K-Means** (MacQueen, 1967) is centroid-based. It minimises within-cluster variance by alternately assigning points to the nearest centroid and updating the centroids:

$$J = \sum_{j=1}^{k} \sum_{x_i \in C_j} \lVert x_i - \mu_j \rVert^2$$

- **Agglomerative hierarchical clustering** builds a nested tree by repeatedly merging the closest clusters. Ward linkage (Ward, 1963) merges the pair that least increases total within-cluster variance.
- **DBSCAN** (Ester et al., 1996) is density-based. It grows clusters from dense neighbourhoods defined by a radius ε and a minimum point count, and labels isolated points as noise.

::: table table_techniques

## 3.3 Dimensionality Reduction with PCA

Principal Component Analysis (Pearson, 1901) was applied to the standardised features. With only three inputs, PCA is not required to counter the curse of dimensionality; its role is to provide a faithful two-dimensional plane for visualising and interpreting clusters. The first two components retain **78.7%** of total variance ([[fig05_pca_variance_biplot]], [[table_pca]]). **PC1 (48.6%)** loads positively on sales (0.64) and stock (0.65) and negatively on price (−0.42): it measures *commercial traction*. **PC2 (30.1%)** is dominated by price (0.91): it measures *price tier*. The PCA plane is therefore directly interpretable in business terms.

::: table table_pca
::: figure fig05_pca_variance_biplot | Explained variance (left) and loading biplot (right) of the principal components.

# 4. Model Implementation and Evaluation {#evaluation}

## 4.1 K-Means

K-Means was fitted with k-means++ initialisation, 20 restarts and a fixed seed (42) for k = 2 to 10 ([[table_kscan]], [[fig06_kmeans_elbow_silhouette]]). Inertia falls by 38.9% between k = 2 and k = 4 and flattens thereafter, locating the elbow. Although the silhouette peaks at k = 2 (0.337), a two-way split merely separates high from low volume. **k = 4** achieves the lowest Davies-Bouldin index of all candidates (1.015) with a solid silhouette (0.307), and yields commercially viable segments of 22–31% of listings. All four clusters have positive mean silhouette widths (0.29–0.32) and only 1.0% of listings carry a negative value ([[fig07_kmeans_clusters_silhouette]]).

::: table table_kscan
::: figure fig06_kmeans_elbow_silhouette | Elbow (inertia) and silhouette criteria across k.
::: figure fig07_kmeans_clusters_silhouette | K-Means (k = 4) on the PCA plane and per-cluster silhouette profile.

## 4.2 Hierarchical Clustering

Four linkage criteria were compared on identical Euclidean distances ([[table_linkage]]). Single and average linkage suffer from *chaining*, absorbing 994 and 989 listings respectively into one cluster; complete linkage produces uneven groups (424/388/180/5). **Ward linkage** yields balanced, interpretable groups (358/237/235/167) and the highest silhouette among linkages (0.253). Its dendrogram separates into four branches at a merge height of roughly 21 ([[fig09_ward_dendrogram_cut]]), supporting a four-cluster cut that also enables a like-for-like comparison with K-Means. Agreement between the two partitions is moderate (ARI 0.41).

$$\Delta(A,B) = \frac{n_A\, n_B}{n_A + n_B} \lVert \mu_A - \mu_B \rVert^2$$

::: table table_linkage
::: figure fig09_ward_dendrogram_cut | Ward dendrogram with the four-cluster cut.

## 4.3 DBSCAN

MinPts was set to 6 (twice the dimensionality) and ε was read from the sorted 6-nearest-neighbour distance curve ([[fig10_dbscan_k_distance]]), followed by a 32-configuration grid search. The curve rises smoothly without a clear knee — the first sign that the catalogue lacks dense, separated regions. Small radii (ε ≤ 0.35) fragment the data and reject 13–89% of listings as noise; larger radii (ε ≥ 0.5) merge almost everything into one cluster. The best compromise (**ε = 0.45**) places 904 listings (90.7%) in one cluster, 4 in a second and 89 (8.9%) in noise, with a slightly negative silhouette (−0.014) ([[fig11_dbscan_clusters]]).

This is an informative negative result: the listings form a **continuum** of price and performance rather than density islands, so DBSCAN cannot segment them. Its noise set nevertheless has a distinct profile — lower prices (median $26 vs $36), higher sales (163 vs 46 units) and thinner stock (5 vs 9) — which makes DBSCAN useful as an anomaly detector.

::: figure fig10_dbscan_k_distance | Sorted 6-nearest-neighbour distances used to select ε.
::: figure fig11_dbscan_clusters | DBSCAN partition on the PCA plane; grey points are noise.

## 4.4 Evaluation Framework

Accuracy-type metrics require ground-truth labels and are therefore inapplicable to clustering. Model quality was instead triangulated across complementary measures, each answering a different question ([[table_metrics]]). The silhouette coefficient (Rousseeuw, 1987) is defined for each listing as:

$$s(i) = \frac{b(i) - a(i)}{\max\{a(i),\, b(i)\}}$$

where a(i) is the mean distance to its own cluster and b(i) to the nearest other cluster. Davies-Bouldin (Davies and Bouldin, 1979) and Calinski-Harabasz (Caliński and Harabasz, 1974) capture compactness relative to separation, while the Adjusted Rand Index (Hubert and Arabie, 1985) measures agreement between partitions and underpins the stability tests.

::: table table_metrics

## 4.5 Comparative Results

::: table table_comparison
::: figure fig12_model_comparison | Side-by-side comparison of internal validity and stability.

K-Means leads on **every internal index** — silhouette 0.307 versus 0.253 (Ward) and −0.014 (DBSCAN), Davies-Bouldin 1.015 versus 1.257 and 1.172, Calinski-Harabasz 503.3 versus 402.9 and 3.5. Stability is decisive: across 30 resamples of 80% of the data, K-Means reproduces its partition almost exactly (**ARI 0.932 ± 0.025**), whereas Ward does not (0.481 ± 0.084) because early merges in a hierarchy are irreversible and small sample changes propagate up the tree.

Sensitivity tests confirm robustness to analytical choices ([[table_sensitivity]]): different random seeds (mean ARI 0.984, minimum 0.951) and removal of the top 1% of sellers (0.937) barely alter the solution, which also shows that the log transform neutralised outlier leverage. Only the switch to min-max scaling (0.492) materially changes the partition, justifying the standardisation decision.

::: table table_sensitivity
::: callout Model Selection Decision
**K-Means (k = 4)** is selected as the production segmentation engine: best internal validity, near-perfect stability and full catalogue coverage. Ward is retained as a structural cross-check and DBSCAN as an operational anomaly flag.
:::

# 5. Cluster Characteristics {#clusters}

Mapping centroids back to business units reveals four distinct commercial segments ([[table_profiles]], [[fig13_cluster_profiles]], [[fig14_cluster_distributions]]):

- **Cluster 2 — Best-Sellers (242 listings, 24.3%).** The revenue engine: **92.3% of all units sold** (710,124 of 769,317), median 952 units at an accessible $29.94, full stock and 99.6% US dispatch. Predominantly Eau de Toilette from high-demand lines such as Armaf and Ralph Lauren.
- **Cluster 0 — Premium Designer (219 listings, 22.0%).** The prestige tier: highest prices (median $68.99, up to $259.09) with steady but slow demand (median 43 units, 3.7% of volume). Concentrated Eau de Parfum from Giorgio Armani, Paco Rabanne and Yves Saint Laurent.
- **Cluster 1 — Budget Commodities (224 listings, 22.5%).** The cheapest offers (median $18.99) yet weak traction (median 30 units, 1.8% of volume), with the highest share of unbranded and generic items: low price alone does not create demand without brand equity.
- **Cluster 3 — Low-Stock Tail (312 listings, 31.3%).** The largest segment: median stock of only 3 units, 14.1% showing "Last One" and minimal sales (median 16 units, 2.2% of volume) — an imminent stock-out and churn risk.

::: table table_profiles
::: explorer
::: figure fig13_cluster_profiles | Standardised feature means per cluster.
::: figure fig14_cluster_distributions | Price, sales and stock distributions within each cluster.

<!-- count:task2 -->
::: part Task 2 | Critical Report for Executive Stakeholders

# 6. Executive Summary {#executive-summary}

Machine learning reveals that our 997 fragrance listings fall into **four natural commercial segments**. One quarter of listings — the best-sellers — generate **92% of all units sold**, while almost a third of the catalogue is close to running out of stock. The recommended model, **K-Means with four segments**, is the most accurate and stable of the three techniques tested and is simple enough to run automatically on new listings. Each segment calls for a distinct action: protect, grow, reposition or audit.

::: kpis

# 7. Critical Evaluation {#critical-evaluation}

## 7.1 Suitability of the Methods and Design Decisions

Unsupervised clustering is the right tool because the company holds no labelled outcomes; the aim is discovery rather than prediction. Three design decisions shaped the outcome. The log transformation stopped a handful of viral listings from dictating the segmentation. The choice of price, sales and stock answers the three questions managers actually ask — *what is it worth, does it sell, will it run out?* Excluding brand and country from the distance calculation prevented segments from degenerating into brand lists. Each decision was tested rather than assumed: the result survives changes of seed and the removal of top sellers.

## 7.2 Comparative Performance: Strengths and Limitations

**K-Means** was the strongest model on every measure. Its limitation is that it assumes compact, similarly sized groups and requires the number of segments to be chosen; on a continuous catalogue its boundaries are therefore soft, as the moderate silhouette (0.31) honestly reflects. **Ward hierarchical clustering** offers an intuitive tree of nested groups but proved unstable: its segments changed substantially whenever the sample changed, and it cannot assign new listings without rebuilding the tree. **DBSCAN** excels at irregular shapes and outlier detection, but because our listings form a continuum it placed 91% of them in one group and left 9% unassigned. These weaknesses are properties of the data as much as of the algorithms, which is itself a valuable insight into how the marketplace is structured.

## 7.3 Why K-Means Is the Right Choice for E-Commerce

Technical scores are only half the decision. An e-commerce platform needs a model that covers every listing, can be refreshed frequently, scores new listings instantly, scales to millions of offers and can be explained to managers ([[table_ecom]]). K-Means satisfies all five requirements: each new listing is assigned to its nearest centroid in microseconds, and each centroid reads as a typical price, sales level and stock position. A simple sales ranking would not suffice either: it identifies who sells most, but not who is premium, who is cheap yet stagnant, or who is about to run out. Segmentation combines all three dimensions into groups that each require a different response.

::: table table_ecom

# 8. Recommendations for Business Managers {#recommendations}

The four segments translate into targeted, measurable interventions ([[fig17_segment_actions]]):

::: figure fig17_segment_actions | Share of listings versus share of units sold per segment, with the recommended action.
::: recs

Implementation should begin with the best-sellers and the low-stock tail, which protect the most revenue for the least effort. Success should be tracked through stock-outs in Cluster 2, the proportion of Cluster 3 listings restocked or delisted within 30 days, and sales per advertising dollar in Cluster 1. The segmentation should be refreshed monthly, with new listings scored on arrival and DBSCAN noise points reviewed as potential anomalies.

# 9. Limitations {#limitations}

The platform caps visible stock at ten units, so genuine depth above that level is unknown. The data is a single snapshot of one product family, so segment boundaries may differ in other categories or seasons. Clusters describe association, not causation: a premium price does not itself make a listing slow. Finally, because listings form a continuum, those near a boundary could reasonably belong to either neighbouring segment; the segments should guide prioritisation rather than replace commercial judgement.

# 10. Conclusion and Future Work {#conclusion}

This project demonstrates that a carefully prepared, well-validated K-Means model can turn an unlabelled and messy catalogue into four clear, actionable segments, and that the commercial value of the catalogue is extraordinarily concentrated. The most important lesson is that **data preparation mattered more than algorithm choice**: recovering values from listing text and correcting the hidden stock ceiling changed the outcome more than any hyperparameter. Equally, DBSCAN's failure was not wasted effort; it provided the clearest evidence that the marketplace is a continuum rather than a set of discrete niches.

Future work would enrich the feature space with revenue, margin and true stock counts, incorporate text embeddings of product descriptions, and track segment migration over time to detect listings that are rising or declining. Validating whether segment membership predicts next-quarter sales would convert the descriptive model into a forward-looking decision tool, and a lightweight dashboard would place each listing's segment directly in the hands of category managers.

<!-- count:none -->
# References {#references}

- Caliński, T. and Harabasz, J. (1974) 'A dendrite method for cluster analysis', *Communications in Statistics*, 3(1), pp. 1–27.
- Davies, D.L. and Bouldin, D.W. (1979) 'A cluster separation measure', *IEEE Transactions on Pattern Analysis and Machine Intelligence*, PAMI-1(2), pp. 224–227.
- Ester, M., Kriegel, H.-P., Sander, J. and Xu, X. (1996) 'A density-based algorithm for discovering clusters in large spatial databases with noise', in *Proceedings of the Second International Conference on Knowledge Discovery and Data Mining*. Portland: AAAI Press, pp. 226–231.
- Hubert, L. and Arabie, P. (1985) 'Comparing partitions', *Journal of Classification*, 2(1), pp. 193–218.
- MacQueen, J. (1967) 'Some methods for classification and analysis of multivariate observations', in *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability*. Berkeley: University of California Press, pp. 281–297.
- McKinney, W. (2010) 'Data structures for statistical computing in Python', in *Proceedings of the 9th Python in Science Conference*, pp. 56–61.
- Müller, A.C. and Guido, S. (2016) *Introduction to Machine Learning with Python*. Sebastopol: O'Reilly Media.
- Pearson, K. (1901) 'On lines and planes of closest fit to systems of points in space', *Philosophical Magazine*, 2(11), pp. 559–572.
- Pedregosa, F. et al. (2011) 'Scikit-learn: machine learning in Python', *Journal of Machine Learning Research*, 12, pp. 2825–2830.
- Rousseeuw, P.J. (1987) 'Silhouettes: a graphical aid to the interpretation and validation of cluster analysis', *Journal of Computational and Applied Mathematics*, 20, pp. 53–65.
- Ward, J.H. (1963) 'Hierarchical grouping to optimize an objective function', *Journal of the American Statistical Association*, 58(301), pp. 236–244.

# Appendix A: Reproducible Code {#appendix}

The complete Task 1 implementation is a single Jupyter notebook that executes end to end in about 30 seconds on Google Colab or locally, with fixed random seeds (42). All materials — notebook, dataset, figures, tables and code screenshots — are hosted in the project repository: https://github.com/kvmmn/_COM7022_MachineLearning. The full notebook code follows, one screenshot per cell in execution order.

::: appendix

**AI use declaration.** AI tools were used to support structuring and proofreading. All analysis was executed, verified and interpreted by the author, and every reported figure was checked against the notebook output. *(Align wording with the Arden AI policy before submission.)*
