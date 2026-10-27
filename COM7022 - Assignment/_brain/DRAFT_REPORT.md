> **SUPERSEDED (2026-10-27):** this draft contains several stale figures (log-skewness, K-Means vs Ward ARI, DBSCAN noise profile, duplicate count). The current report text is `_brain/REPORT.md` (built into the Word/PDF report and the portal), using the numbers in `output/`.

# COM7022 Coursework Draft: Product Clustering Portfolio

**Student ID:** 25199053  
**Module:** COM7022 Machine Learning  
**Dataset:** `Sales-[5444].csv` (E-commerce Men's Fragrance Listings)  

---

## Task 1: Practical Machine Learning Investigation (Technical Project)

### 1.1 Problem Framing and Data Understanding

This project investigates product segmentation for a fast-growing e-commerce marketplace using an authentic listing catalogue (`Sales-[5444].csv`). In digital marketplaces, cataloguing teams cannot manually inspect thousands of multi-seller offers to adjust promotional priority, identify inventory stock-outs, or isolate premium items from budget commodities. The operational objective is to design, implement, and evaluate an unsupervised machine learning clustering pipeline that groups fragrance listings according to their physical product characteristics and commercial sales performance.

The dataset provides 1,000 raw listing records across 10 attributes, capturing product metadata (`Item_Name`, `details`, `Catatory`), pricing structure (`price`, `priceWithCurrency`), inventory availability and commercial traction (`available`, `text`, `sold`), listing maintenance timestamps (`lastUpdated`), and dispatch provenance (`itemLocation`). 

A critical preliminary methodological decision concerns the unit of observation. While `Item_Name` records brand names such as *Giorgio Armani* (60 listings) or *Ralph Lauren* (41 listings), individual rows represent distinct seller listings rather than unique stock-keeping units (SKUs) or manufacturers. Multiple sellers list identical fragrances with differing price points, remaining quantities, and shipping origins. The clustering pipeline therefore operates at the listing level, providing granular operational intelligence on seller catalogue dynamics.

Initial inspection of the raw records confirmed 0 full-row duplicates, though 39 listings share duplicate text in their `details` description. An audit of data completeness identified missing values across six attributes (Table 1 and Figure 1). The highest incompleteness occurs in `available` (111 missing records, 11.1%) and `lastUpdated` (53 missing records, 5.3%), alongside smaller omissions in `sold` (8 records), `price` (5 records), `Catatory` (3 records), and `Item_Name` (1 record). 

Descriptive statistical profiling of the raw numerical columns reveals acute distributional asymmetries (Table 2 and Figure 2). Listed prices span from \$3.00 to \$259.09, exhibiting moderate right-skewness (skewness = +2.18; median = \$35.71; mean = \$46.43). In contrast, recorded sales volumes display extreme right-skewness (skewness = +11.23; mean = 775.2 units; standard deviation = 3,211.4 units). While the median listing records 49.5 sales, superstar listings exceed 10,000 units, culminating in a catalogue maximum of 54,052 units. Standard Euclidean distance metrics applied directly to these raw scales would collapse cluster boundaries, making sales volume almost entirely dictate cluster formation. Careful non-linear transformation and robust scaling are therefore essential prerequisite steps.

---
*(Section 1.1 Word Count: 372 words)*

### 1.2 Data Preparation and Pre-processing

Rather than applying blind statistical imputation or immediately discarding incomplete rows, data preparation prioritised deterministic recovery from complementary fields within the same listing. Every intervention was recorded in an execution ledger (Table 3).

First, all five missing `price` values were successfully recovered from `priceWithCurrency`, where identical numerical values were preserved as plain text. Across all 995 listings where both price fields coexisted, the extracted figures matched the numeric price exactly with zero discrepancies exceeding \$0.01. Three listings priced in Canadian Dollars (`C $` prefix, all dispatching from Ontario) were converted to US Dollars using a documented fixed rate of 0.73 USD/CAD, establishing currency parity.

Second, the composite `text` string ("... available / ... sold") was parsed to resolve commercial figures. Two missing `sold` values were extracted directly from listing text. Three listings that detailed positive inventory without mentioning prior sales were assigned `sold = 0`, reflecting products that had not yet transacted. Conversely, three rows containing neither listing text nor any sales or inventory data were pruned, reducing the verified dataset from 1,000 to 997 complete listing records.

Third, inventory availability was harmonised to resolve systemic marketplace censoring. Raw marketplace listings obscure exact stock levels exceeding 10 units behind the label *"More than 10 available"* (299 listings). Without adjustment, an uncensored seller listing 50 available units would appear five times larger than a censored seller with 50 units. Consequently, all 299 censored listings were coded as 11, and 115 listings showing explicit quantities above 10 were capped at 11, establishing a robust operational scale where 11 denotes deep stock. Listings showing *"Last One"* (47 rows) were mapped to 1. Unquantified listings displaying *"Limited quantity available"* or wholesale lots (62 rows) were imputed with the median (11) and flagged with a binary indicator (`stock_imputed = 1`).

Fourth, textual categories were standardised. The raw `Catatory` column contained over 50 noisy variants resulting from seller spelling mistakes and inconsistent capitalisation (such as *Eau De Parfum*, *eau de perfume*, and *eau de toillette*). These were harmonised into six coherent fragrance categories: Eau de Toilette (454), Eau de Parfum (300), Cologne (57), Parfum / Extrait (17), Generic Fragrance (32), and Other (137). A single record missing a brand label was classified as *Unbranded*.

Finally, to address acute distributional skewness, natural logarithmic transformations $\log(1 + x)$ were applied to `price` and `sold`. The transformation compressed price skewness from +2.18 to -0.08 and sales skewness from +11.23 to +0.25 (Table 4 and Figure 3). While 141 listings exceed the raw sales upper Tukey fence ($Q_3 + 1.5 \times \text{IQR} = 791$ units), removing them would discard the most commercially successful items in the catalogue. Logarithmic transformation successfully retains these vital business records while preventing extreme values from distorting Euclidean geometry.

---
*(Section 1.2 Word Count: 456 words)*

### 1.3 Feature Selection and Justification

Unsupervised clustering algorithms are highly vulnerable to the inclusion of irrelevant, noisy, or collinear features. To isolate the primary drivers of catalogue segmentation, candidate numerical variables were screened through Spearman rank correlation analysis (Figure 4) and systematic multi-feature silhouette evaluations (Table 5).

The correlation matrix demonstrates that the candidate attributes capture distinct commercial mechanisms without severe collinearity. Price exhibits mild negative associations with units sold ($r_s = -0.14$) and inventory availability ($r_s = -0.16$), confirming that premium fragrances move in lower volumes. Meanwhile, units sold and stock availability display a moderate positive correlation ($r_s = +0.37$), reflecting standard commercial inventory replenishment behind active products.

Five alternative feature subsets were benchmarked across cluster counts $k = 2$ through $k = 6$ (Table 5). A two-variable baseline consisting solely of `log_price` and `log_sold` (Set A) achieved marginally higher silhouette separation (0.351 to 0.377). However, Set A completely ignores stock availability, failing the brief's explicit requirement to capture availability status and obscuring the operational risk of imminent stock-outs. Expanding to the three-variable combination of `log_price`, `log_sold`, and `stock_level` (Set B) maintained robust separation (silhouette 0.297 to 0.337) while incorporating the three core business dimensions: price positioning, commercial demand, and supply stability.

Further expanding the feature space to include `days_since_update` or bottle volume `size_oz` (Sets C, D, and E) eroded clustering quality, dropping silhouette scores to between 0.255 and 0.292. Bottle size lacks operational variance because 75% of fragrance listings are standardised between 3.3 and 3.4 fluid ounces, while listing update recency spans a narrow window without systematic commercial meaning. 

High-cardinality categorical attributes (240+ brands, six fragrance categories, dispatch origins) were deliberately excluded from the distance metric. One-hot encoding sparse categories expands dimensionality, distorts Euclidean distance, and causes clusters to isolate specific brand names rather than general product behaviours. Categorical metadata was instead reserved for post-hoc profiling.

Because distance-based clustering algorithms require variables to contribute equally to Euclidean space, the three selected features in Set B were standardised using z-score standardisation:

$$z = \frac{x - \mu}{\sigma}$$

This scales each feature to a mean of zero and a standard deviation of one, preventing the wider integer spread of `stock_level` (1 to 11) from dominating the compressed log-transformed price and sales scales.

---
*(Section 1.3 Word Count: 368 words)*

### 1.4 Dimensionality Reduction via Principal Component Analysis (PCA)

Principal Component Analysis was applied to the standardised three-dimensional feature space (Pearson, 1901). In low-dimensional problems ($p = 3$), PCA is not required to overcome the curse of dimensionality or filter multicollinearity. Instead, PCA was implemented to provide a rigorous, uncorrupted two-dimensional coordinate system for cluster visualisation and to quantify the orthogonal directions of catalogue variation (Table 6 and Figure 5).

Eigenvalue decomposition demonstrates that the first two principal components capture 78.7% of total catalogue variance (Figure 5, left). The first principal component (PC1) accounts for 48.6% of overall variance, with feature loadings of -0.421 on `log_price`, +0.636 on `log_sold`, and +0.647 on `stock_level`. PC1 represents commercial traction, contrasting high-volume, well-stocked items against slower-moving, high-priced goods. 

The second principal component (PC2) explains an additional 30.1% of catalogue variance, dominated almost entirely by `log_price` with a positive loading of +0.906 (+0.335 on `log_sold`, +0.260 on `stock_level`). PC2 cleanly isolates market luxury tier. The third principal component (PC3) captures the remaining 21.3% of variance.

The resulting biplot (Figure 5, right) projects the listings across the PC1-PC2 plane alongside directional vectors for the three original features. The loading vectors confirm that sales and stock align closely along the positive PC1 axis, whereas price projects orthogonally along positive PC2. This 2D projection serves as the validated visual plane for inspecting the cluster partitions generated by K-Means, Hierarchical, and DBSCAN algorithms.

---
*(Section 1.4 Word Count: 231 words)*

### 1.5 K-Means Clustering

K-Means partitions data by iteratively assigning observations to the nearest cluster centroid and updating centroids to minimise the within-cluster sum of squares (WCSS), or inertia (MacQueen, 1967):

$$J = \sum_{j=1}^{k} \sum_{x_i \in C_j} ||x_i - \mu_j||^2$$

To prevent convergence to suboptimal local minima, K-Means was implemented with k-means++ centroid seeding, running 20 random initialisations (`n_init=20`) under a fixed random seed (42).

Because K-Means requires the cluster count $k$ to be predefined, models were evaluated across $k = 2$ through $k = 10$ (Table 7 and Figure 6). Inertia drops steeply from 1,943.0 at $k=2$ to 1,501.0 at $k=3$ and 1,186.7 at $k=4$, yielding a 38.9% reduction in total variance. Beyond $k=4$, variance reduction flattens noticeably (974.4 at $k=5$, 862.5 at $k=6$), establishing an empirical elbow between $k=3$ and $k=5$.

While the silhouette score attains its global maximum at $k=2$ (0.337), a two-cluster split merely separates high-volume products from low-volume products, collapsing price and inventory variations into trivial aggregates. In contrast, $k=4$ preserves solid silhouette separation (0.307) while achieving the lowest Davies-Bouldin index across all tested specifications (1.015), indicating maximum cluster compactness relative to inter-cluster separation. Furthermore, $k=4$ produces commercially viable segment sizes: the smallest cluster holds 219 listings (22.0%) and the largest holds 312 listings (31.3%), avoiding the uninterpretable micro-clusters observed at $k \ge 7$ (Table 7).

Projected onto the validated PCA plane, the four K-Means clusters form distinct, convex geometric regions (Figure 7, left). A granular silhouette profile per cluster confirms balanced cluster health (Figure 7, right). Average silhouette widths remain positive across all four groups (Cluster 0: 0.31; Cluster 1: 0.28; Cluster 2: 0.33; Cluster 3: 0.30) with negligible negative silhouettes, confirming that observations are closer to their assigned centroids than to neighbouring clusters.

---
*(Section 1.5 Word Count: 297 words)*

### 1.6 Hierarchical Agglomerative Clustering

Hierarchical clustering constructs an unconstrained nested tree of partitions by successively merging the closest pair of clusters without requiring an initial specification of $k$ (Hastie et al., 2009). The agglomeration path depends fundamentally on the chosen linkage metric. To evaluate structural consistency against taught methods, four linkage criteria were executed on identical pairwise Euclidean distances (Table 8 and Figure 8).

Single linkage (nearest-neighbour proximity) generated severe chaining, yielding a high cophenetic correlation ($r = 0.362$) but collapsing 994 listings into one massive cluster while isolating three singleton outliers. Complete linkage (farthest-neighbour proximity, $r = 0.536$) split the catalogue into uneven groups (424, 388, 180, and 5 listings). Average linkage (UPGMA, $r = 0.631$) reproduced the chaining defect, merging 989 listings into a single group.

Ward's minimum-variance linkage (Ward, 1963) proved vastly superior for business segmentation. Rather than computing pairwise point distances, Ward merges the pair of clusters that produces the smallest increase in total within-cluster variance:

$$\Delta \text{ESS}_{AB} = \frac{n_A n_B}{n_A + n_B} ||\mu_A - \mu_B||^2$$

Ward linkage produced balanced, interpretable partitions (358, 237, 235, and 167 listings) with a silhouette score of 0.253 at $k=4$ (Table 8). 

Pruning the Ward dendrogram with a horizontal cut at merge distance 18.5 yields four distinct branches (Figure 9). Across cluster counts $k = 2$ to $k = 10$, Ward's silhouette peaks at $k=2$ (0.324) and stabilises at 0.253 for $k=4$ (Table 9). Cross-tabulating the Ward $k=4$ partition against the K-Means $k=4$ solution produces an Adjusted Rand Index (ARI) of 0.468. This moderate concordance indicates that while both algorithms identify broadly similar catalogue poles, Ward's greedy, irreversible hierarchical merges constrain point assignments differently from K-Means iterative centroid relocations.

---
*(Section 1.6 Word Count: 282 words)*

### 1.7 Density-Based Spatial Clustering (DBSCAN)

DBSCAN discovers clusters of arbitrary geometric shape by identifying contiguous high-density regions separated by areas of low point density (Ester et al., 1996). Unlike K-Means and Ward linkage, DBSCAN does not assume spherical clusters, requires no predefined cluster count $k$, and explicitly designates sparse peripheral observations as noise (-1).

DBSCAN behaviour is governed by two hyperparameters: the neighbourhood search radius ($\epsilon$) and the minimum number of points required to form a dense core ($\text{MinPts}$). Following standard heuristic guidelines for low-dimensional spaces, $\text{MinPts}$ was initialised to $2 \times p = 6$. A sorted $k$-distance plot evaluated the Euclidean distance from every point to its 6th nearest neighbour (Figure 10). The resulting curve displays a smooth, continuous gradient without a sharp inflection knee, demonstrating that product listings do not occupy disconnected dense density peaks.

A systematic grid search evaluated 32 parameter configurations across $\epsilon \in [0.25, 0.70]$ and $\text{MinPts} \in [4, 15]$ (Table 10). Tighter radii ($\epsilon \le 0.35$) fragmented the catalogue into dozens of uninterpretable micro-clusters while rejecting between 22.9% and 88.6% of listings as noise. Wider radii ($\epsilon \ge 0.50$) collapsed virtually the entire dataset into a single indiscriminate mass.

The optimal compromise setting was identified at $\epsilon = 0.45$ and $\text{MinPts} = 6$ (Table 10). This model detected two clusters alongside 89 noise points (8.9% of listings). However, inspection of the resulting partition reveals severe structural asymmetry (Figure 11): Cluster 0 captures 904 listings (90.7%), Cluster 1 isolates a tiny pocket of 4 listings (0.4%), and 89 listings are discarded. The silhouette score on clustered records is slightly negative (-0.014), with a Calinski-Harabasz score of only 3.5.

This empirical result provides a vital analytical finding: authentic e-commerce catalogues represent continuous multi-attribute spectra rather than isolated density islands. DBSCAN is fundamentally unsuited as a primary market segmentation engine. Nevertheless, profiling the 89 noise observations reveals that DBSCAN functions effectively as an automated anomaly detector, flagging extreme high-price items (median \$85.00), ultra-high-volume listings, and extreme supply imbalances.

---
*(Section 1.7 Word Count: 334 words)*

### 1.8 Model Comparison, Validation, and Model Choice

Because unsupervised learning lacks ground-truth target labels, model evaluation combined internal cluster validation indices, statistical stability benchmarking via bootstrap resampling, and sensitivity stress tests (Table 11 and Figure 12).

Internal validation decisively favours K-Means. K-Means achieves a silhouette score of 0.307, outperforming Ward hierarchical clustering (0.253) and DBSCAN (-0.014 on clustered points). It also achieves the lowest Davies-Bouldin index (1.015 versus 1.257 for Ward and 1.172 for DBSCAN) and the highest Calinski-Harabasz score (503.3 versus 402.9 for Ward and 3.5 for DBSCAN), demonstrating superior compactness and cluster separation.

To test algorithmic stability against sampling variance, models were evaluated across 30 independent bootstrap runs using 80% random sub-sampling, measuring cluster agreement against the full-dataset baseline with the Adjusted Rand Index (Hubert and Arabie, 1985). K-Means exhibited exceptional resampling stability, achieving an average ARI of $0.932 \pm 0.025$. In contrast, Ward hierarchical clustering demonstrated acute instability, recording an average ARI of only $0.481 \pm 0.084$. Because agglomerative hierarchical clustering makes rigid, irreversible merges at early iterations, minor perturbations in sample composition propagate upward, fundamentally reordering subsequent cluster branches. DBSCAN achieved moderate stability on its core cluster ($0.749 \pm 0.063$) but failed to generate actionable partitions.

Robustness and sensitivity analyses further substantiated the K-Means specification (Table 12). Re-running K-Means across 10 random seeds confirmed near-perfect initialisation invariance (mean pairwise ARI = 0.984; minimum = 0.936). To evaluate vulnerability to extreme sales volumes, the top 1% volume listings (> 11,000 units sold) were temporarily trimmed; K-Means retained an ARI of 0.937 on the remaining 987 listings, proving that the logarithmic pre-processing successfully immunised the model against outlier leverage. 

However, substituting z-score standardisation with min-max normalisation reduced cluster concordance to ARI = 0.492. Min-max scaling bounds each attribute to $[0, 1]$, which disproportionately amplifies the bounded integer scale of `stock_level` (1 to 11) relative to the wider continuous spreads of log-transformed price and volume. Standardisation was retained because it preserves equal empirical feature variance ($s^2 = 1$).

On both technical validation metrics and operational business requirements, **K-Means ($k=4$) is selected as the primary segmentation engine**. Unlike DBSCAN, K-Means assigns 100% of catalogue listings to actionable clusters without unassigned noise. In production, its fixed centroid coordinates enable immediate, low-latency $O(k)$ classification of incoming product listings. Ward linkage is retained as an analytical structural benchmark (ARI concordance = 0.468), while DBSCAN is repurposed as an automated anomaly detection monitor.

---
*(Section 1.8 Word Count: 395 words)*

### 1.9 Cluster Characteristics and Business Relevance

Translating the selected K-Means ($k=4$) cluster centroids back into original financial and inventory units reveals four distinct commercial product segments across the 997 verified listings (Table 13, Table 14, and Figures 13 and 14).

**Cluster 2: Best-Sellers (High-Velocity Volume Drivers)**  
Representing 242 listings (24.3% of the catalogue), this cluster forms the commercial engine of the marketplace. While comprising under a quarter of listings, Cluster 2 accounts for **92.3% of total catalogue sales volume** (710,030 transacted units out of 769,045 total; mean = 2,934 units; median = 952 units). Listings occupy an accessible mid-tier price point (median \$29.94) and maintain deep inventory (median stock = 11, only 1.2% displaying *"Last One"*). Geographically, 99.6% dispatch from the United States, and 67.8% are Eau de Toilette sprays. Brand profiling identifies highly sought-after commercial fragrances, including *Armaf* (notably *Club de Nuit Intense Man*), *Ralph Lauren*, and accessible lines from *Giorgio Armani*.

**Cluster 0: Premium Designer Fragrances (High-Margin Prestige)**  
Comprising 219 listings (22.0% of the catalogue), this segment captures prestige market positioning. Listed at the highest price points (median \$68.99, reaching \$259.09), these products exhibit deliberate, low-velocity sales traction (median = 43 units, mean = 131 units), contributing 3.7% of catalogue volume. Inventory depth is substantial (median stock = 11, 0% *"Last One"*), with 84.9% shipping from the US. Reflecting premium formulation, 45.2% are concentrated Eau de Parfum and 6.4% Parfum/Extrait, dominated by elite luxury fashion houses: *Giorgio Armani*, *Paco Rabanne*, and *Yves Saint Laurent*.

**Cluster 1: Budget Commodities and Dupe Fragrances (Low-Traction Mass Market)**  
Covering 224 listings (22.5% of the catalogue), this segment occupies the entry-level price tier (median \$18.99). Despite low consumer prices, commercial velocity remains sluggish (median = 30 units, mean = 61 units; 1.8% of catalogue volume). Sellers maintain deep inventory (median stock = 11, 0% *"Last One"*). This segment concentrates the catalogue's mass-market and alternative items: it holds 37.9% Eau de Toilette, 14.3% generic fragrances, the highest proportion of *Unbranded* listings (39 records), and Middle Eastern dupe brands (such as *Lattafa*). The sluggish sales volume demonstrates that low pricing alone does not generate velocity without established brand equity.

**Cluster 3: Low-Stock and Discontinued Tail (Depleted Supply Risk)**  
The largest segment by listing count (312 listings, 31.3%), this group captures listings facing critical inventory depletion. Median stock availability is restricted to just 3 units, with **14.1% of listings displaying *"Last One"***. Commercial traction is stagnant (median = 16 units, mean = 54 units; 2.2% of catalogue volume) at a moderate median price of \$39.99. Composed of casual sellers liquidating remaining stock or discontinued product runs across diverse brands, these listings represent imminent stock-out churn that requires catalogue replenishment or delisting.

---
*(Section 1.9 Word Count: 442 words)*

---

## Task 2: Critical Evaluation and Executive Report

### 2.1 Executive Summary

This executive report translates the machine learning investigation undertaken on our 1,000-listing fragrance catalogue into strategic commercial intelligence. Rapid catalogue expansion across thousands of uncurated third-party merchant listings creates severe operational risks: capital allocation becomes inefficient, high-demand inventory faces unexpected stock-outs, and marketing spend is squandered on slow-moving products.

Using an unsupervised machine learning clustering architecture, the catalogue was segmented along three core commercial dimensions: pricing tier, cumulative sales traction, and merchant stock availability. The analysis evaluated three distinct machine learning methodologies (K-Means, Ward Hierarchical Clustering, and DBSCAN). Rigorous empirical validation confirmed K-Means ($k=4$) as the most robust, stable, and operationally viable production model.

The investigation uncovered a critical revenue concentration: **24.3% of listings (Cluster 2: Best-Sellers) generate 92.3% of total historical transaction volume**. Conversely, 31.3% of the catalogue (Cluster 3) is operating under acute inventory depletion, with nearly one in seven listings down to its final unit. These findings form the basis of four targeted operational interventions spanning supply protection, premium basket building, promotional reallocations, and catalogue hygiene.

---
*(Section 2.1 Word Count: 182 words)*

### 2.2 Method Suitability and Pre-processing Decisions

Unsupervised machine learning is uniquely suited to marketplace catalogue analysis because e-commerce platforms lack predefined operational labels. Unlike supervised learning, which requires historical conversion tags or manual annotations, unsupervised clustering discovers natural, data-driven behavioural groupings directly from observable product and merchant attributes.

The choice of features directly determined analytical success. Raw text categories contained over 50 noisy misspellings and capitalisation errors, while listing descriptions contained over 240 disparate brand names. Feeding one-hot encoded categorical variables into distance calculations was deliberately rejected: sparse binary indicators inflate mathematical dimensionality and cause algorithms to group listings by superficial brand names rather than underlying commercial behaviours. 

Instead, the model selected three standardised numerical features: log-transformed price, log-transformed sales volume, and harmonised stock availability. Marketplace listings obscure stock levels above 10 units behind the label *"More than 10 available"*. Rather than discarding these records, inventory availability was capped at 11, transforming an unquantified string into a reliable index of inventory depth.

Logarithmic transformation of price and sales proved essential. While median sales volume is 49.5 units, top-tier commercial listings reach up to 54,052 units. Direct application of standard Euclidean distance to raw figures would cause the sales dimension to exert overwhelming mathematical leverage, collapsing all non-bestselling items into a single undifferentiated mass. Logarithmic compression reduced sales skewness from +11.23 to +0.25, ensuring that price tier and inventory status contribute equally to customer segment boundaries while keeping every high-volume listing in the analysis.

---
*(Section 2.2 Word Count: 260 words)*

### 2.3 Critical Comparative Evaluation of Machine Learning Models

Three contrasting clustering paradigms were benchmarked on the standardised catalogue data: centroid-based partitioning (K-Means), agglomerative tree construction (Hierarchical Ward Linkage), and density-based spatial scanning (DBSCAN). Each method relies on distinct mathematical assumptions that directly govern its commercial utility (Table 11 and Figure 12).

**K-Means Partitioning**  
K-Means assumes that data clusters are convex, spherical, and of broadly comparable variance. While consumer marketplaces form continuous spectrums rather than disjoint geometric spheres, K-Means proved exceptionally effective for commercial segmentation. It produced the cleanest cluster separation (silhouette width = 0.307; Davies-Bouldin index = 1.015) and delivered near-perfect statistical stability ($0.932 \pm 0.025$ Adjusted Rand Index across 30 bootstrap resamples). Its main theoretical limitation is the requirement to predetermine $k$; however, this was resolved through rigorous elbow inflection analysis and silhouette profiling.

**Hierarchical Agglomerative Clustering (Ward Linkage)**  
Hierarchical clustering was evaluated using four linkage methods. Single and average linkages suffered from severe chaining defects, merging over 98% of listings into a single mega-cluster. Ward's minimum-variance linkage produced balanced clusters but scored lower than K-Means across all internal validation metrics (silhouette = 0.253; Davies-Bouldin = 1.257). Crucially, bootstrap resampling revealed acute structural fragility (stability ARI = $0.481 \pm 0.084$). Because hierarchical clustering makes permanent, greedy merge decisions at early iterations, minor shifts in catalogue sampling fundamentally reshape downstream segment assignments.

**DBSCAN Density-Based Scanning**  
DBSCAN attempts to locate dense spatial clusters separated by empty regions. Across 32 parameter configurations (Table 10), DBSCAN proved fundamentally incompatible with marketplace catalogue data. Because retail listings form a continuous gradient of price and sales rather than isolated spatial clusters, DBSCAN merged 90.7% of listings into one generic cluster while discarding 8.9% of listings as unclustered noise. Although unsuitable for segmentation, DBSCAN provides high utility as an operational anomaly detector.

---
*(Section 2.3 Word Count: 312 words)*

### 2.4 Justification of Final Model Selection

The selection of **K-Means ($k=4$)** as the primary production engine is justified by both technical validation metrics and operational business requirements:

1. **Superior Partition Quality:** K-Means delivered the highest silhouette score (0.307), lowest Davies-Bouldin index (1.015), and highest Calinski-Harabasz separation (503.3) among all evaluated algorithms.
2. **Exceptional Operational Stability:** Resampling stability of 0.932 ARI ensures that segment definitions remain consistent over time, avoiding the erratic cluster reassignments exhibited by Ward linkage (0.481 ARI). Sensitivity testing confirmed that K-Means is resilient to random seed initialisations (0.984 ARI) and volume outliers (0.937 ARI).
3. **Complete Catalogue Coverage:** Unlike DBSCAN, which abandoned 89 listings as unclassified noise, K-Means partitions 100% of the active catalogue into actionable commercial tiers.
4. **Production Scalability:** K-Means model parameters consist of four static 3D centroid vectors. In production, classifying a newly onboarded seller listing requires trivial Euclidean distance calculation to each centroid ($O(k)$ complexity), enabling instantaneous, real-time segment tagging within the live ingestion pipeline.

---
*(Section 2.4 Word Count: 178 words)*

### 2.5 Strategic Evidence-Based Recommendations

Drawing on the empirical characteristics of the four discovered segments (Table 13 and Figures 13 and 14), management should execute four coordinated commercial initiatives:

```
[Catalogue Revenue Engine: 997 Listings]
       │
       ├──► Cluster 2 (24.3% listings | 92.3% sales) ──► PROTECT: Priority SLAs & Replenishment
       ├──► Cluster 0 (22.0% listings |  3.7% sales) ──► GROW:   Prestige Bundling & Content
       ├──► Cluster 1 (22.5% listings |  1.8% sales) ──► TRIM:   Reduce Spend & Seller Fees
       └──► Cluster 3 (31.3% listings |  2.2% sales) ──► AUDIT:  Restock Outreach & Delisting
```

**1. Secure the Core Revenue Engine (Cluster 2: Best-Sellers)**  
*Finding:* Cluster 2 accounts for 92.3% of total catalogue volume (median sales 952 units at \$29.94), concentrated in accessible US-dispatched Eau de Toilette lines (*Armaf*, *Ralph Lauren*).  
*Action:* Establish automated inventory guardrails. Implement algorithmic restock alerts when merchant stock dips below 10 units, and offer reduced marketplace commission tiers (for example, a 1.5% fee discount) to top merchants who maintain 99% dispatch reliability. A stock-out in this cluster immediately harms platform gross merchandise volume (GMV).

**2. Elevate Premium Margin Realisation (Cluster 0: Prestige Designer)**  
*Finding:* Cluster 0 captures luxury fashion houses (*Giorgio Armani*, *Paco Rabanne*, *YSL*) at premium price points (median \$68.99, max \$259.09) with steady, low-velocity demand (median 43 units).  
*Action:* Position these items as basket builders. Deploy personalized cross-selling widgets on product detail pages, bundling Cluster 2 best-sellers with complementary Cluster 0 travel sprays. Introduce authenticated merchant badges to assure consumers of product provenance, lifting conversion rates on high-margin stock.

**3. Reposition Low-Traction Mass Commodities (Cluster 1: Budget Fragrances)**  
*Finding:* Despite aggressive pricing (median \$18.99), Cluster 1 generates only 1.8% of sales volume, concentrating unbranded items and generic dupes. Low price does not drive sales without brand awareness.  
*Action:* Cease platform-funded paid search campaigns on unbranded items. Shift low-performing listings to organic algorithmic search ranking and reallocate performance marketing budgets toward proven Cluster 2 lines.

**4. Mitigate Tail Inventory Depletion (Cluster 3: Low-Stock Tail)**  
*Finding:* Cluster 3 represents 31.3% of all listings but operates under critical stock depletion (median stock 3 units; 14.1% *"Last One"*), generating negligible turnover (median 16 sales).  
*Action:* Institute a 30-day supplier replenishment audit. Automated notices should prompt merchants to restock depleted lines. Listings that remain unreplenished and record zero transactions over 60 days should be automatically retired from active search indexing, cleaning catalogue clutter and reducing buyer bounce rates from out-of-stock listings.

---
*(Section 2.5 Word Count: 376 words)*

### 2.6 Operational Limitations and Continuous Improvement Roadmap

To ensure rigorous executive governance, three analytical limitations must be acknowledged:

1. **Marketplace Stock Censoring:** The marketplace platform caps visible stock availability at 10 units. While capping at 11 resolved scale distortion, it obscures the difference between a merchant holding 15 units and a distributor holding 500 units. Negotiating API-level integration with enterprise sellers to capture uncensored warehouse inventory is recommended.
2. **Observational Cross-Sectional Data:** The dataset captures a static snapshot in May 2024. Observed sales reflect cumulative historical volume rather than daily run-rates. Establishing automated daily batch ingestion will enable dynamic time-series tracking of listing velocity.
3. **Scaling Sensitivity:** Sensitivity tests demonstrated that min-max scaling yields alternative boundaries (ARI = 0.492). While z-score standardisation is technically justified by variance parity, ongoing validation should monitor whether merchant price changes disproportionately shift products across segment boundaries.

---
*(Section 2.6 Word Count: 147 words)*

---

## References

- Caliński, T. and Harabasz, J. (1974) 'A dendrite method for cluster analysis', *Communications in Statistics*, 3(1), pp. 1-27.
- Davies, D.L. and Bouldin, D.W. (1979) 'A cluster separation measure', *IEEE Transactions on Pattern Analysis and Machine Intelligence*, PAMI-1(2), pp. 224-227.
- Ester, M., Kriegel, H.-P., Sander, J. and Xu, X. (1996) 'A density-based algorithm for discovering clusters in large spatial databases with noise', in *Proceedings of the Second International Conference on Knowledge Discovery and Data Mining (KDD-96)*, Portland, Oregon, pp. 226-231.
- Géron, A. (2022) *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*. 3rd edn. Sebastopol: O'Reilly Media.
- Hastie, T., Tibshirani, R. and Friedman, J. (2009) *The Elements of Statistical Learning: Data Mining, Inference, and Prediction*. 2nd edn. New York: Springer.
- Hubert, L. and Arabie, P. (1985) 'Comparing partitions', *Journal of Classification*, 2(1), pp. 193-218.
- Hunter, J.D. (2007) 'Matplotlib: A 2D graphics environment', *Computing in Science & Engineering*, 9(3), pp. 90-95.
- Lloyd, S. (1982) 'Least squares quantization in PCM', *IEEE Transactions on Information Theory*, 28(2), pp. 129-137.
- MacQueen, J. (1967) 'Some methods for classification and analysis of multivariate observations', in *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability*, 1, pp. 281-297.
- McKinney, W. (2010) 'Data structures for statistical computing in Python', in *Proceedings of the 9th Python in Science Conference*, Austin, Texas, pp. 56-61.
- Müller, A.C. and Guido, S. (2016) *Introduction to Machine Learning with Python: A Guide for Data Scientists*. Sebastopol: O'Reilly Media.
- Pearson, K. (1901) 'On lines and planes of closest fit to systems of points in space', *Philosophical Magazine*, 2(11), pp. 559-572.
- Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M. and Duchesnay, E. (2011) 'Scikit-learn: machine learning in Python', *Journal of Machine Learning Research*, 12, pp. 2825-2830.
- Rousseeuw, P.J. (1987) 'Silhouettes: a graphical aid to the interpretation and validation of cluster analysis', *Journal of Computational and Applied Mathematics*, 20, pp. 53-65.
- Virtanen, P. et al. (2020) 'SciPy 1.0: fundamental algorithms for scientific computing in Python', *Nature Methods*, 17(3), pp. 261-272.
- Ward, J.H. (1963) 'Hierarchical grouping to optimize an objective function', *Journal of the American Statistical Association*, 58(301), pp. 236-244.
