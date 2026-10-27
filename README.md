# COM7022 — Machine Learning

**Arden University Berlin** · MSc Data Science · Student ID **25199053**  
Module: **COM7022 Machine Learning**  
Assignment: **Product Segmentation and Performance Clustering (Portfolio)**  

---

### Final report and review page
- **Final report (Word):** [`COM7022 - Assignment/COM7022_Portfolio_25199053_final.docx`](COM7022%20-%20Assignment/COM7022_Portfolio_25199053_final.docx) and [PDF](COM7022%20-%20Assignment/COM7022_Portfolio_25199053_final.pdf). Task 1 and Task 2 in one document, about 3,900 words of body text, full code in Appendix A as screenshots.
- **Review page (GitHub Pages):** [https://kvmmn.github.io/_COM7022_MachineLearning/](https://kvmmn.github.io/_COM7022_MachineLearning/) shows the same report with an interactive segment explorer.
- **Notebook (executed on Google Colab, with outputs):** [`COM7022 - Assignment/COM7022_Clustering_25199053.ipynb`](COM7022%20-%20Assignment/COM7022_Clustering_25199053.ipynb)
- **Dataset:** [`COM7022 - Assignment/Sales-[5444].csv`](COM7022%20-%20Assignment/Sales-%5B5444%5D.csv)
- **Code screenshots:** `COM7022 - Assignment/output/screenshots/` (body) and `.../appendix/` (every notebook cell)

**Single source of truth:** all report text lives in `COM7022 - Assignment/_brain/REPORT.md`. The Word/PDF report and the GitHub Pages portal are both generated from it, so they always match.

**Code layout:** all analysis code, figures, tables and diagrams live in the Colab notebook. The only script is `COM7022 - Assignment/scripts/build_report.py`, which assembles the deliverables from the notebook outputs (code screenshots, Word + PDF report, portal). **Rebuild:** run the notebook, then `python "COM7022 - Assignment/scripts/build_report.py"` (needs LibreOffice and poppler; optional argument `shots`, `docx` or `html` runs one step).

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
| `index.html` | GitHub Pages copy of the final report with interactive cluster explorer (built by `scripts/build_report.py`) |

---

## Technical Summary

- **Problem:** E-commerce multi-seller fragrance catalogue segmentation based on physical characteristics and sales performance.
- **Data Hygiene:** 1,000 raw listings processed to 997 verified records; deterministic recovery of prices and sales from text; resolution of marketplace inventory censoring (capping at 11); natural log transformation compressing sales skewness from +9.72 to +0.52.
- **Feature Space:** Log-transformed price, log-transformed sales volume, and inventory availability scale; standardised via z-score scaling.
- **PCA Dimensionality Analysis:** First two principal components capture 78.7% of total variance (PC1 = 48.6% commercial traction; PC2 = 30.1% price luxury tier).
- **Random seed:** always 274.
- **Evaluated Algorithms:** K-Means ($k=4$), Hierarchical Agglomerative Clustering (Ward Linkage), DBSCAN ($\epsilon=0.45, \text{MinPts}=6$), HDBSCAN (min cluster size 30, min samples 6) and the TabClustPFN tabular foundation model (automatic k and k = 4).
- **Primary Production Model:** K-Means ($k=4$), chosen for superior partition metrics (Silhouette = 0.307; Davies-Bouldin = 1.013; Calinski-Harabasz = 503.3), near-perfect resampling stability ($0.929 \pm 0.033$ ARI), and complete catalogue coverage.
- **Discovered Segments:**
  1. *Cluster 2 (Best-Sellers):* 24.3% of listings driving **90.7% of platform sales volume** (median $29.76, median sales 918 units).
  2. *Cluster 0 (Prestige Designer):* 22.7% of listings (median $67.14, median sales 42 units).
  3. *Cluster 1 (Budget Commodities):* 21.7% of listings (median $18.10, median sales 30 units).
  4. *Cluster 3 (Low-Stock Tail):* 31.4% of listings under critical inventory depletion (median stock 3 units, 14.7% *"Last One"*).
