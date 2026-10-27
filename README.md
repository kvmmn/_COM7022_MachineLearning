# COM7022 — Machine Learning

**Arden University Berlin** · MSc Data Science · Student ID **25199053**  
Module: **COM7022 Machine Learning**  
Assignment: **Product Segmentation and Performance Clustering (Portfolio)**  

---

### Coursework Interactive Review Draft (GitHub Pages)
The full interactive assessment draft (Task 1 Technical Project & Task 2 Executive Report) is published live on GitHub Pages:  
👉 **[https://kvmmn.github.io/_COM7022_MachineLearning/](https://kvmmn.github.io/_COM7022_MachineLearning/)**

- Direct self-contained review file path in repository: [`COM7022 - Assignment/COM7022_Draft_Review_25199053.html`](COM7022%20-%20Assignment/COM7022_Draft_Review_25199053.html)
- Executable Colab-ready notebook: [`COM7022 - Assignment/COM7022_Clustering_25199053.ipynb`](COM7022%20-%20Assignment/COM7022_Clustering_25199053.ipynb)
- Dataset: [`COM7022 - Assignment/Sales-[5444].csv`](COM7022%20-%20Assignment/Sales-%5B5444%5D.csv)

---

## Layout

| Folder / File | What it holds |
|---|---|
| `COM7022 - Assignment/` | Coursework materials, Jupyter notebook, scripts, and generated figures/tables |
| `COM7022 - Assignment/_brain/` | Assignment operating system (control, decision log, source ledger, results ledger, draft report) |
| `COM7022 - Assignment/output/` | High-resolution figures (`figures/`) and structured CSV metrics tables (`tables/`) |
| `COM7022 - Code Space/` | Seminar notebooks, Colab activities, and reference code |
| `COM7022 - Lessons/` | Module lecture slides, transcripts, and reading material |
| `COM7022 - eBooks/` | Reference textbooks |
| `index.html` | Self-contained GitHub Pages portfolio report with interactive cluster explorer |

---

## Technical Summary

- **Problem:** E-commerce multi-seller fragrance catalogue segmentation based on physical characteristics and sales performance.
- **Data Hygiene:** 1,000 raw listings processed to 997 verified records; deterministic recovery of prices and sales from text; resolution of marketplace inventory censoring (capping at 11); natural log transformation compressing sales skewness from +9.72 to +0.52.
- **Feature Space:** Log-transformed price, log-transformed sales volume, and inventory availability scale; standardised via z-score scaling.
- **PCA Dimensionality Analysis:** First two principal components capture 78.7% of total variance (PC1 = 48.6% commercial traction; PC2 = 30.1% price luxury tier).
- **Evaluated Algorithms:** K-Means ($k=4$), Hierarchical Agglomerative Clustering (Ward Linkage), and DBSCAN ($\epsilon=0.45, \text{MinPts}=6$).
- **Primary Production Model:** K-Means ($k=4$), chosen for superior partition metrics (Silhouette = 0.307; Davies-Bouldin = 1.015; Calinski-Harabasz = 503.3), near-perfect resampling stability ($0.932 \pm 0.025$ ARI), and complete catalogue coverage.
- **Discovered Segments:**
  1. *Cluster 2 (Best-Sellers):* 24.3% of listings driving **92.3% of platform sales volume** (median $29.94, median sales 952 units).
  2. *Cluster 0 (Prestige Designer):* 22.0% of listings (median $68.99, median sales 43 units).
  3. *Cluster 1 (Budget Commodities):* 22.5% of listings (median $18.99, median sales 30 units).
  4. *Cluster 3 (Low-Stock Tail):* 31.3% of listings under critical inventory depletion (median stock 3 units, 14.1% *"Last One"*).
