#!/usr/bin/env python3
"""Build the final COM7022 report (.docx) from the notebook outputs.

Structure follows the tutor feedback and the assessment brief:
  Introduction -> Task 1 (data prep, model selection, evaluation, profiles) -> Task 2 (critical report).
Every figure/screenshot carries a caption that points to its file in the GitHub repository.
Code is shown as screenshots only; the full notebook is linked in Appendix A.

Run:  python "COM7022 - Assignment/scripts/04_build_report_docx.py"
"""
import re
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
FIGS, SHOTS, TABLES = OUT / "figures", OUT / "screenshots", OUT / "tables"
DOCX = ROOT / "COM7022_Portfolio_25199053_final.docx"

STUDENT_ID = "25199053"
REPO = "https://github.com/kvmmn/_COM7022_MachineLearning"
BASE = REPO + "/blob/main/COM7022%20-%20Assignment/"
REPO_PATH = "COM7022 - Assignment/"
MIDNIGHT = RGBColor(0x00, 0x2B, 0x49)
TIFFANY = RGBColor(0x00, 0x8F, 0x8B)

doc = None
counted_words = {}
section_tag = "Intro"
fig_n = 0
tab_n = 0
LABELS = {}      # key -> "Figure n" / "Table n" (filled on pass 1, used on pass 2)
NEW_LABELS = {}


def ref(text):
    """Replace [[key]] with the caption label of that figure/table (resolved on the second pass)."""
    return re.sub(r"\[\[([a-z0-9_]+)\]\]", lambda m: LABELS.get(m.group(1), "?"), text)


# ---------------------------------------------------------------- styling helpers
def setup():
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Calibri", Pt(10.5)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.12
    for name, size in (("Heading 1", 17), ("Heading 2", 13), ("Heading 3", 11)):
        h = doc.styles[name]
        h.font.name, h.font.size, h.font.bold = "Calibri", Pt(size), True
        h.font.color.rgb = MIDNIGHT
        h.paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10)
        h.paragraph_format.space_after = Pt(4)
        h.element.rPr.rFonts.set(qn("w:asciiTheme"), "minorHAnsi") if False else None
    # footer with student ID + page number
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"COM7022 Machine Learning  |  Student ID {STUDENT_ID}  |  Page ")
    r.font.size = Pt(8.5)
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        run = p.add_run()
        run.font.size = Pt(8.5)
        if tag:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), tag); run._r.append(el)
        else:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = text; run._r.append(el)


def count(text):
    n = len(re.findall(r"[A-Za-z0-9£$%][A-Za-z0-9'’.,£$%/+\-=<>]*", text))
    counted_words[section_tag] += n


def add_runs(p, text):
    """Very small inline markup: **bold** and *italic*."""
    text = ref(text)
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if part.startswith("**"):
            p.add_run(part[2:-2]).bold = True
        elif part.startswith("*") and len(part) > 2:
            p.add_run(part[1:-1]).italic = True
        elif part:
            p.add_run(part)


def para(text, counted=True, style=None):
    text = ref(text)
    p = doc.add_paragraph(style=style)
    add_runs(p, text)
    if counted:
        count(re.sub(r"\*", "", text))
    return p


def bullets(items):
    for t in items:
        para(t, style="List Bullet")


def heading(text, level=2):
    doc.add_heading(text, level=level)


def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def caption(kind, text, repo_file=None, key=None):
    """Caption + small pointer to the exact file in the GitHub repo (excluded from word count)."""
    global fig_n, tab_n
    if kind == "Figure":
        fig_n += 1; label = f"Figure {fig_n}"
    elif kind == "Table":
        tab_n += 1; label = f"Table {tab_n}"
    else:
        label = kind
    if key:
        NEW_LABELS[key] = label
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(f"{label}. {text}")
    r.italic = True; r.font.size = Pt(9)
    if repo_file:
        r2 = p.add_run(f"  Source file: {REPO_PATH}{repo_file}  |  {BASE}{repo_file.replace(' ', '%20')}")
        r2.font.size = Pt(8); r2.font.color.rgb = TIFFANY
    return label


def picture(path, caption_text, repo_rel, width_cm=15.5):
    doc.add_picture(str(path), width=Cm(width_cm))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.keep_with_next = True
    kind = "Figure" if "figures" in repo_rel else "Screenshot"
    if kind == "Screenshot":
        global fig_n
        fig_n += 1
        label = f"Figure {fig_n}"
        NEW_LABELS[Path(repo_rel).stem] = label
        p = doc.add_paragraph()
        r = p.add_run(f"{label}. Code screenshot: {caption_text}")
        r.italic = True; r.font.size = Pt(9)
        r2 = p.add_run(f"  Source file: {REPO_PATH}{repo_rel}  |  {BASE}{repo_rel.replace(' ', '%20')}")
        r2.font.size = Pt(8); r2.font.color.rgb = TIFFANY
        return label
    return caption("Figure", caption_text, repo_rel, key=Path(repo_rel).stem)


def table(df, caption_text, repo_file=None, col_widths=None, font=8.5, key=None):
    rows, cols = df.shape
    t = doc.add_table(rows=rows + 1, cols=cols)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, c in enumerate(df.columns):
        cell = t.cell(0, j)
        cell.text = ""
        run = cell.paragraphs[0].add_run(str(c)); run.bold = True; run.font.size = Pt(font)
        run.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_bg(cell, "002B49")
    for i in range(rows):
        for j in range(cols):
            cell = t.cell(i + 1, j)
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(df.iat[i, j])); run.font.size = Pt(font)
            if i % 2: set_cell_bg(cell, "F2F5F7")
    if col_widths:
        for j, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[j].width = Cm(w)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(1)
    caption("Table", caption_text, repo_file, key=key)


def read(name, **kw):
    return pd.read_csv(TABLES / name, **kw)


# ---------------------------------------------------------------- content
def title_page():
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run("COM7022 Machine Learning"); r.font.size = Pt(30); r.bold = True; r.font.color.rgb = MIDNIGHT
    p = doc.add_paragraph()
    r = p.add_run("Product Segmentation and Performance Clustering"); r.font.size = Pt(18); r.font.color.rgb = TIFFANY
    p = doc.add_paragraph()
    r = p.add_run("Portfolio: Task 1 (Practical Project) and Task 2 (Critical Report)"); r.font.size = Pt(12)
    doc.add_paragraph()
    for k, v in (("Student ID", STUDENT_ID), ("Module", "COM7022 Machine Learning, Assignment [5444]"),
                 ("Programme", "MSc Data Science, Arden University Berlin"),
                 ("Dataset", "Sales-[5444].csv (1,000 e-commerce fragrance listings)"),
                 ("GitHub repository (all materials)", REPO),
                 ("Notebook", REPO_PATH + "COM7022_Clustering_25199053.ipynb"),
                 ("Word count", "WORDCOUNT_PLACEHOLDER")):
        p = doc.add_paragraph()
        r = p.add_run(f"{k}:  "); r.bold = True
        p.add_run(v)
    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run("All figures, tables and code screenshots in this report are saved in the GitHub repository above. "
                  "The caption under each one names the exact file.")
    r.italic = True; r.font.size = Pt(9.5)
    doc.add_page_break()


def intro():
    global section_tag
    section_tag = "Intro"
    heading("1. Introduction", 1)
    heading("1.1 The company and the business context", 2)
    para("I joined a fast-growing online marketplace as a Machine Learning Analyst. The company lets many independent sellers "
         "list the same kinds of products side by side, so its catalogue grows faster than any team can review by hand. "
         "Managers must still decide which listings to promote, which to restock and which to retire. They currently have "
         "no systematic way to tell a fast-selling staple from a slow premium item or a listing that is about to run out.")
    heading("1.2 The data", 2)
    para("The company supplied one file, `Sales-[5444].csv`, with **1,000 product listings and 10 columns**. "
         "The listings are men’s fragrances. Each row holds the product name and description, a category label, the price, "
         "the stock shown to buyers, a text field with stock and units sold, the last update time and the item location. "
         "Each row is one seller’s listing, not one unique product, so the clusters describe listings.".replace("`", ""))
    heading("1.3 The problem", 2)
    para("Three problems stand in the way of a data-driven catalogue. The catalogue is too large to review manually. "
         "The data is messy: values are missing, category names are inconsistent, and exact stock above 10 units is hidden. "
         "Finally, there are no labels that say which listing is a “best-seller” or a “slow mover”, so a supervised model cannot "
         "be trained. The company needs a way to **discover** the natural groups in its own data.")
    heading("1.4 Objectives", 2)
    para("My own objectives for this project are:")
    bullets([
        "**O1. Prepare** the data so that every cleaning decision is evidence-based and reported.",
        "**O2. Group** listings by product characteristics and sales performance using K-Means, Hierarchical clustering and DBSCAN.",
        "**O3. Evaluate** the models with several different metrics, not one, and say what each metric can and cannot tell us.",
        "**O4. Choose** the model that is best technically and best for an e-commerce business.",
        "**O5. Translate** the segments into actions that non-technical managers can use.",
    ])
    heading("1.5 Approach and method", 2)
    para("I followed the standard machine learning workflow shown in [[fig15_workflow]]: understand the problem, audit and clean the data, "
         "transform and scale it, select features, reduce dimensions with PCA for viewing, fit three clustering techniques, "
         "evaluate them, choose one, profile the segments and turn them into business actions. All work is in Python "
         "(pandas, scikit-learn, SciPy, matplotlib) in one notebook that runs end to end on Google Colab with fixed random seeds. "
         "The notebook was re-run from scratch before writing this report, and it reproduced every number below.")
    para("The report has two parts. Task 1 documents the practical work: data preparation, model selection and evaluation. "
         "Task 2 is the critical report for managers: why K-Means was chosen, how the models performed, what the company should do "
         "and where the work could go next. Every figure, table and code screenshot names the file in the GitHub repository that produced it, "
         "so a reader can check any result.")
    picture(FIGS / "fig15_workflow.png", "End-to-end workflow followed in this project.", "output/figures/fig15_workflow.png", 16)


def task1_data_prep():
    global section_tag
    section_tag = "Task 1"
    heading("Task 1: Practical Project", 1)
    heading("2. Data preparation", 1)
    heading("2.1 Data audit: missing values and quality", 2)
    para("I first inspected the file for missing values, duplicates, skew and dirty labels. There are no duplicate rows. "
         "Six columns have gaps, the largest being `available` (111 rows, 11.1%) and `lastUpdated` (53 rows, 5.3%) "
         "([[table_missing]] and [[fig01_missing_values]]).".replace("`", ""))
    para("The audit exposed four issues that would mislead a clustering algorithm. **First**, price and units sold are strongly "
         "right-skewed: the most-sold listing has 54,052 sales against a median of about 50 (skewness 9.70). **Second**, the stock "
         "figure is **censored**: the marketplace shows “More than 10 available” and stores it as 10 (299 listings, including two lot-based listings). "
         "**Third**, 63 distinct category labels are really spelling and capitalisation variants of a handful of product types. "
         "**Fourth**, three prices are in Canadian dollars.")
    mv = read("table01_missing_values.csv")
    mv.columns = ["Column", "Missing", "Missing %"]
    mv = mv[mv["Missing"] > 0]
    table(mv, "Missing values per column in the raw file (1,000 rows).", "output/tables/table01_missing_values.csv", [5, 3, 3], key="table_missing")
    picture(FIGS / "fig01_missing_values.png", "Missing values by column.", "output/figures/fig01_missing_values.png", 11)

    heading("2.2 Cleaning and pre-processing", 2)
    para("My rule was to **recover** a missing value from another column of the same row before imputing anything, and to impute only "
         "where the reason for the gap is understood. Every step was written to a cleaning log ([[table_cleaning]]). In brief:")
    bullets([
        "**Price and units sold** were recovered from the text columns `priceWithCurrency` and `text` (5 prices, 2 sales figures), "
        "and the three Canadian-dollar prices were converted to US dollars.".replace("`", ""),
        "**Stock level** was rebuilt from the listing wording. “More than 10” and any larger number were capped at 11 so every row "
        "is on one scale, “Last One” became 1, and 62 “Limited quantity” rows received the median, with a flag column to mark them.",
        "**Product type**: the 63 category labels were merged into six clean types (Eau de Toilette, Eau de Parfum, Cologne, "
        "Parfum / Extrait, Generic fragrance, Other).",
        "**Unusable rows**: three listings with neither sales nor stock information were dropped, leaving **997 listings**.",
    ])
    para("**Why recover instead of impute?** Filling gaps with an average hides the reason a value is missing. Here the reason is known: "
         "the marketplace writes “Last One” or “Limited quantity” instead of a number, so the wording itself carries information. "
         "Recovering from the same row keeps each listing’s real values. The only imputation is the median for 62 stock values, flagged in a column "
         "so the effect could be checked. No listing was removed as an outlier, because the best-sellers are exactly the listings the business cares about.")
    log = read("table03_cleaning_log.csv", index_col=0)
    log.columns = ["Step", "Rows affected", "Note"]
    table(log, "Cleaning log: every pre-processing step with the number of rows affected.",
          "output/tables/table03_cleaning_log.csv", [6.2, 2, 8], key="table_cleaning")
    picture(FIGS / "fig16_data_prep_flow.png", "Data preparation flow from raw file to model-ready data.",
            "output/figures/fig16_data_prep_flow.png", 16)
    para("The screenshots below show the code behind these steps (the full code is in the notebook and in Appendix A).", counted=True)
    for stem, cap in (("code01_import_data", "importing the data"), ("code02_missing_values", "missing-value audit"),
                      ("code03_price_recovery", "recovering price"), ("code04_sold_recovery", "recovering units sold"),
                      ("code05_stock_level", "rebuilding stock level and handling censoring"),
                      ("code06_product_type", "normalising product type")):
        picture(SHOTS / f"{stem}.png", cap, f"output/screenshots/{stem}.png", 15)

    heading("2.3 Transformation, scaling and categorical variables", 2)
    para("**Log transform.** Distance-based clustering is dominated by extreme values, and sales are extremely skewed. I applied "
         "log(1 + x) to price and units sold, which keeps the best-sellers in the data but stops them from dominating the distances "
         "([[fig03_transformed_distributions]]). After cleaning, the skewness of units sold falls from 9.72 to 0.52 and of price from 1.97 to 0.09 ([[table_clean_desc]]).")
    para("**Scaling.** I used z-score standardisation so that each feature has mean 0 and standard deviation 1. "
         "Min-max scaling was tested as a sensitivity check and changed the grouping substantially (agreement 0.49, Section 4.4), "
         "because it exaggerates the narrow 1 to 11 stock scale.")
    para("**Categorical variables.** Brand has 246 distinct values, so one-hot encoding would add hundreds of columns and let a single "
         "brand drive the distances. Product type, brand and country were therefore kept out of the distance calculation and used afterwards "
         "to describe the clusters.")
    para("These choices were tested rather than assumed. In the sensitivity checks (Section 4.4) K-Means gave almost the same groups with "
         "a different seed and with the top 1% of sellers removed, so the pre-processing makes the result robust. It only failed with a different scaling method, "
         "which is why scaling is documented as a deliberate decision.")
    d = read("table04_descriptive_statistics_clean.csv", index_col=0).loc[["price", "sold", "stock_level", "log_price", "log_sold"],
                                                                        ["count", "mean", "std", "min", "50%", "max", "skewness"]]
    d.insert(0, "Variable", d.index)
    d = d.rename(columns={"50%": "median"})
    table(d, "Descriptive statistics after cleaning (997 listings), including skewness before and after the log transform.",
          "output/tables/table04_descriptive_statistics_clean.csv", font=8, key="table_clean_desc")
    picture(FIGS / "fig03_transformed_distributions.png", "Distributions after the log transform.",
            "output/figures/fig03_transformed_distributions.png", 15.5)
    picture(SHOTS / "code07_log_transform.png", "log transform", "output/screenshots/code07_log_transform.png", 14)
    picture(SHOTS / "code08_scaling.png", "standard scaling of the selected features", "output/screenshots/code08_scaling.png", 14)

    heading("2.4 Feature selection", 2)
    para("The brief asks for groups based on product characteristics and sales performance, so I screened candidate features with a "
         "Spearman correlation matrix ([[fig04_feature_correlation]]) and compared five feature sets by silhouette score ([[table_featuresets]]). I selected "
         "**log price, log units sold and stock level** (Set B). They give three distinct business views: market position, sales "
         "performance and availability. Set A (price and sales only) scores slightly higher but ignores availability, which the business needs "
         "to spot stock-outs. Adding days since update or bottle size lowered the scores and added little meaning.")
    fs = read("table05_feature_set_scan.csv")
    fs.columns = ["Feature set", "Features", "k=2", "k=3", "k=4", "k=5", "k=6"]
    table(fs, "Silhouette score of K-Means for five feature sets (higher is better).",
          "output/tables/table05_feature_set_scan.csv", [5.6, 1.6, 1.5, 1.5, 1.5, 1.5, 1.5], key="table_featuresets")
    picture(FIGS / "fig04_feature_correlation.png", "Spearman correlation between candidate features.",
            "output/figures/fig04_feature_correlation.png", 9.5)


def task1_models():
    heading("3. Model selection", 1)
    heading("3.1 What is clustering?", 2)
    para("Clustering is **unsupervised learning**: the algorithm finds groups of similar items without being told the right answer. "
         "Listings in the same cluster are similar to each other and different from listings in other clusters. "
         "That fits this problem because the company has no labels for its listings.")
    heading("3.2 The three techniques", 2)
    mt = pd.DataFrame([
        ["K-Means", "Places k centres and assigns each listing to the nearest one, then moves the centres until stable.",
         "Fast, simple, every listing gets a group, easy to explain.", "Needs k in advance; assumes round, similar-sized groups."],
        ["Hierarchical (Ward)", "Starts with every listing alone and merges the most similar pair step by step; the result is a tree (dendrogram).",
         "No need to fix k; the tree shows structure.", "Merges are final; slow on large data; sensitive to sampling."],
        ["DBSCAN", "Grows groups from dense regions and labels isolated listings as noise.",
         "Finds odd shapes; flags outliers; no k needed.", "Needs a dense, well-separated structure and careful settings."],
    ], columns=["Technique", "How it works", "Strengths", "Weaknesses"])
    table(mt, "The three clustering techniques compared.", None, [2.8, 5.6, 4.2, 4.4], font=8.5, key="table_techniques")
    heading("3.3 Dimensionality reduction with PCA", 2)
    para("With three features PCA is not needed to remove noise, but I used it to draw all clusters on one two-dimensional map. "
         "The first two components keep **78.7%** of the variance (PC1 48.6%, PC2 30.1%). PC1 behaves like commercial traction "
         "(sales and stock load positively, price negatively) and PC2 like price tier (loading 0.91 on log price), so the map has "
         "a business meaning ([[fig05_pca_variance_biplot]]).")
    para("PCA also served as a check on the feature choice. All three features load strongly on the first two components, so none is redundant, "
         "and the third component (21.3% of variance) mainly contrasts sales with stock. It adds detail but is not needed for viewing the groups.")
    picture(FIGS / "fig05_pca_variance_biplot.png", "PCA explained variance (left) and feature loadings (right).",
            "output/figures/fig05_pca_variance_biplot.png", 15.5)
    picture(SHOTS / "code09_pca.png", "PCA", "output/screenshots/code09_pca.png", 14)


def task1_eval():
    heading("4. Implementation and evaluation", 1)
    heading("4.1 K-Means", 2)
    para("I scanned k from 2 to 10 using the elbow in inertia and three indices ([[table_kscan]]). The silhouette is highest at k = 2 (0.337), "
         "but two groups only separate “sells” from “does not sell”. At **k = 4** inertia has dropped 39% from k = 2, "
         "the Davies-Bouldin index is the lowest of all (1.015), and every cluster still holds at least 22% of the listings.")
    para("K-Means used k-means++ starting points, 20 restarts per fit and a fixed seed (42), so the answer is repeatable. "
         "The map in [[fig07_kmeans_clusters_silhouette]] shows four regions arranged along traction (PC1) and price (PC2), with soft borders where "
         "neighbouring groups meet. That is what a continuum looks like, and it explains why the silhouette is moderate rather than high.")
    ks = read("table07_kmeans_k_scan.csv")
    ks.columns = ["k", "Inertia", "Silhouette", "Davies-Bouldin", "Calinski-Harabasz", "Smallest cluster"]
    table(ks, "K-Means scan: inertia and validation indices for k = 2 to 10.", "output/tables/table07_kmeans_k_scan.csv",
          [1.2, 2.4, 2.6, 3, 3.4, 3], key="table_kscan")
    picture(FIGS / "fig06_kmeans_elbow_silhouette.png", "Elbow (inertia) and silhouette against k.",
            "output/figures/fig06_kmeans_elbow_silhouette.png", 12)
    picture(FIGS / "fig07_kmeans_clusters_silhouette.png", "K-Means clusters on the PCA map (left) and silhouette profile (right).",
            "output/figures/fig07_kmeans_clusters_silhouette.png", 15.5)
    picture(SHOTS / "code10_kmeans_scan.png", "scanning k for K-Means", "output/screenshots/code10_kmeans_scan.png", 14)

    heading("4.2 Hierarchical clustering", 2)
    para("Following the taught approach I compared four linkages on the same distances ([[table_linkage]]). Single and average linkage "
         "put 994 and 989 listings into one cluster (“chaining”), and complete linkage gave very uneven groups. **Ward** linkage gave "
         "balanced groups (358, 237, 235 and 167 listings) and the best silhouette (0.253), so I carried it forward. "
         "Its grouping agrees only moderately with K-Means (Adjusted Rand Index 0.41).")
    para("The dendrogram ([[fig09_ward_dendrogram_cut]]) splits into four branches at a merge distance of about 21, so a four-cluster cut is reasonable "
         "and matches K-Means, which lets the two methods be compared on equal terms. The branches are still unstable under resampling, as Section 4.4 shows.")
    lk = read("table08_linkage_comparison.csv")
    lk.columns = ["Linkage", "Cophenetic correlation", "Silhouette at k = 4", "Cluster sizes"]
    table(lk, "Four linkage methods compared on the same data.", "output/tables/table08_linkage_comparison.csv", [3, 4, 4, 4.5], key="table_linkage")
    picture(FIGS / "fig09_ward_dendrogram_cut.png", "Ward dendrogram cut at four clusters.",
            "output/figures/fig09_ward_dendrogram_cut.png", 12)
    picture(SHOTS / "code11_hierarchical.png", "four linkages", "output/screenshots/code11_hierarchical.png", 14)

    heading("4.3 DBSCAN", 2)
    para("I set min_samples to 6 (twice the number of features) and read eps from the k-distance curve, then tested 32 combinations "
         "([[fig10_dbscan_k_distance]], [[fig11_dbscan_clusters]]; the full grid is saved in output/tables/table10_dbscan_grid.csv). Small eps values (0.35 or below) split the data into many tiny groups and call 23% to 89% of listings noise; larger values "
         "merge everything. The best compromise, **eps = 0.45**, still puts 904 listings (90.7%) in one cluster, 4 in another and 89 (8.9%) "
         "in noise. The silhouette on clustered points is slightly negative (-0.014). The k-distance curve has no sharp knee because "
         "listings form a continuum, not separate dense islands. DBSCAN is therefore a poor segmenter here, but its noise points are "
         "useful: they are cheaper (median $26 against $36), sell more (median 163 against about 46 units) and carry less stock (5 against 9).")
    picture(FIGS / "fig10_dbscan_k_distance.png", "Sorted k-distance curve used to choose eps.",
            "output/figures/fig10_dbscan_k_distance.png", 11)
    picture(FIGS / "fig11_dbscan_clusters.png", "DBSCAN result on the PCA map; grey points are noise.",
            "output/figures/fig11_dbscan_clusters.png", 11)
    picture(SHOTS / "code12_dbscan_kdist.png", "DBSCAN k-distance", "output/screenshots/code12_dbscan_kdist.png", 14)

    heading("4.4 Evaluation with several metrics", 2)
    para("Accuracy cannot be used because there are no true labels. I therefore combined five kinds of evidence, "
         "each answering a different question ([[table_metrics]]).")
    mx = pd.DataFrame([
        ["Silhouette", "How much closer a listing is to its own cluster than to the next one (-1 to 1).", "Higher",
         "Says nothing about stability or usefulness; penalises DBSCAN’s uneven shapes."],
        ["Davies-Bouldin", "Average similarity between each cluster and its closest rival (compactness vs separation).", "Lower",
         "Favours round clusters."],
        ["Calinski-Harabasz", "Ratio of between-cluster to within-cluster spread.", "Higher",
         "Rises with convex clusters; unreliable for DBSCAN."],
        ["Stability (ARI)", "Agreement of labels when 20% of listings are dropped (30 repeats). 1 = identical.", "Higher",
         "Shows whether the groups are real or an accident of the sample."],
        ["Sensitivity", "Agreement after changing seed, scaling method or removing the top 1% of sellers.", "Higher",
         "Tests robustness to my own choices."],
        ["Noise % and cluster sizes", "Share of listings left unassigned and the smallest and largest cluster.", "Low noise, balanced",
         "Business metric: can every listing be acted on?"],
    ], columns=["Metric", "What it measures", "Better when", "Limitation"])
    table(mx, "Evaluation metrics: what each one measures and what it cannot tell us.", None, [2.8, 6.2, 2.2, 5.8], font=8.5, key="table_metrics")
    cmp_ = read("table11_model_comparison.csv")
    cmp_ = cmp_[["model", "clusters", "noise_pct", "silhouette", "davies_bouldin", "calinski_harabasz", "stability_ARI_mean",
                 "smallest_cluster_pct", "largest_cluster_pct"]]
    cmp_.columns = ["Model", "Clusters", "Noise %", "Silhouette", "Davies-Bouldin", "Calinski-Harabasz", "Stability ARI",
                    "Smallest %", "Largest %"]
    table(cmp_, "Model comparison on all metrics (K-Means is best or equal-best on every column except cluster-size balance).",
          "output/tables/table11_model_comparison.csv", font=8, key="table_comparison")
    picture(FIGS / "fig12_model_comparison.png", "Side-by-side comparison of the three models.",
            "output/figures/fig12_model_comparison.png", 15.5)
    para("**K-Means wins on every internal index** (silhouette 0.307, Davies-Bouldin 1.015, Calinski-Harabasz 503) and on stability "
         "(ARI 0.93 ± 0.03 against 0.48 for Ward). It is also robust to my own choices: different seeds give ARI 0.98, "
         "removing the top 1% of sellers gives 0.94, but switching to min-max scaling gives only 0.49, which is why I standardised. "
         "Ward’s tree is unstable because early merges cannot be undone.")
    para("**How to read these numbers.** A silhouette of 0.31 is commonly read as moderate structure: listings are on average closer to their own "
         "group than to another, but the groups touch. This agrees with the continuous shape seen in the PCA map. The Davies-Bouldin and "
         "Calinski-Harabasz indices rank the models in the same order as the silhouette, which gives more confidence than any single index. "
         "Stability adds something the indices cannot: a model can score well and still change when the sample changes, as Ward does. "
         "DBSCAN’s scores are not directly comparable because they ignore the 8.9% of listings it calls noise.")
    sens = read("table12_sensitivity_checks.csv")
    sens.columns = ["Sensitivity check", "ARI"]
    table(sens, "Sensitivity checks on the K-Means solution.", "output/tables/table12_sensitivity_checks.csv", [9, 2.5])
    picture(SHOTS / "code13_metrics.png", "evaluation metrics function", "output/screenshots/code13_metrics.png", 14)
    picture(SHOTS / "code14_stability.png", "stability across random subsamples", "output/screenshots/code14_stability.png", 14)


def task1_profiles():
    heading("5. Cluster characteristics", 1)
    para("Translated back into business units ([[table_profiles]], [[fig13_cluster_profiles]] and [[fig14_cluster_distributions]]), the four K-Means clusters of the 997 listings are:")
    bullets([
        "**Cluster 2, Best-sellers (242 listings, 24.3%).** They deliver **92.3% of all units sold** (median 952 units) at a median price of "
        "$29.94, with full stock and 99.6% shipped from the US. Mostly Eau de Toilette; brands include Armaf and Ralph Lauren.",
        "**Cluster 0, Premium designer (219 listings, 22.0%).** The highest prices (median $68.99, up to $259.09), steady but slow sales "
        "(median 43 units, 3.7% of volume), deep stock. Mostly Eau de Parfum from Giorgio Armani, Paco Rabanne and Yves Saint Laurent.",
        "**Cluster 1, Budget (224 listings, 22.5%).** The lowest prices (median $18.99) but weak sales (median 30 units, 1.8% of volume). "
        "It holds the most unbranded and generic items, so low price alone does not create demand.",
        "**Cluster 3, Low-stock tail (312 listings, 31.3%).** The largest group: median stock of only 3 units, 14.1% marked “Last One”, "
        "median 16 units sold (2.2% of volume).",
    ])
    cp = read("table13_cluster_profiles.csv", index_col=0).T
    cp = cp.loc[["listings", "share_of_listings_pct", "median_price_usd", "median_units_sold", "share_of_units_sold_pct",
                 "median_stock_level", "pct_last_one", "top_product_type"]]
    cp.insert(0, "Measure", ["Listings", "Share of listings %", "Median price (US$)", "Median units sold", "Share of units sold %",
                             "Median stock level", "% marked Last One", "Top product type"])
    cp.columns = ["Measure", "Cluster 0 Premium", "Cluster 1 Budget", "Cluster 2 Best-seller", "Cluster 3 Low-stock"]
    table(cp, "Profile of the four K-Means segments.", "output/tables/table13_cluster_profiles.csv", [4, 3, 3, 3.4, 3.2], key="table_profiles")
    picture(FIGS / "fig13_cluster_profiles.png", "Cluster profiles as standardised feature means.",
            "output/figures/fig13_cluster_profiles.png", 14)
    picture(FIGS / "fig14_cluster_distributions.png", "Price, units sold and stock distributions inside each cluster.",
            "output/figures/fig14_cluster_distributions.png", 15.5)


def task2():
    global section_tag
    section_tag = "Task 2"
    doc.add_page_break()
    heading("Task 2: Critical Report for Executives", 1)
    heading("6. Executive summary", 1)
    para("Our 997 fragrance listings fall into **four natural segments**. One quarter of them, the best-sellers, generate **92% of all units sold**. "
         "The other three segments (premium, budget and low-stock listings) together account for 8% of sales and need three different treatments. "
         "I recommend **K-Means with four clusters** as the company’s segmentation model: it is the most accurate, the most stable and the "
         "simplest to run on new listings. The groups overlap somewhat, as is normal for real catalogues, so they should guide decisions, "
         "not replace judgement.")
    heading("7. Why this model, and why for this dataset", 1)
    heading("7.1 Suitability of the methods and decisions", 2)
    para("Unsupervised clustering suits the problem because the company has no labels. Three decisions mattered most. Log scaling stopped a handful of "
         "viral listings from controlling the result. Choosing price, sales and stock as features answered the three questions managers ask "
         "(what is it worth, does it sell, will it run out). Keeping brand and country out of the distance calculation prevented clusters "
         "from simply being brand lists.")
    heading("7.2 How the models performed", 2)
    para("K-Means led on all internal metrics and on stability ([[table_comparison]], [[fig12_model_comparison]]). Ward was moderately good but changed whenever the sample "
         "changed. DBSCAN found almost no structure: 90.7% of listings in one cluster and 8.9% noise. "
         "This is informative rather than a failure: the listings sit on a continuum from budget to premium and from slow to fast, "
         "so methods that assume gaps between groups cannot work well. A silhouette of about 0.31 confirms the groups are meaningful but "
         "not sharply separated.")
    para("**Strengths and limits of each model.** *K-Means* is fast, stable and explainable, but it assumes round groups of similar size and needs k chosen "
         "in advance; here a continuum makes the borders soft. *Ward* shows how groups nest and needs no k, but it is unstable and cannot score new listings. "
         "*DBSCAN* is ideal for finding outliers and irregular shapes, but this catalogue has no empty gaps between groups, so it merges most listings into one "
         "cluster. No model is perfect for this data; K-Means has the fewest weaknesses that matter to the business.")
    heading("7.3 Which model is best for e-commerce?", 2)
    para("Technical scores are only half the decision. A marketplace also needs a model that covers every listing, can be re-run "
         "every week, can score a new listing instantly and can be explained to a manager ([[table_ecom]]). K-Means meets all of these. "
         "Ward cannot score new listings without re-building the tree. DBSCAN leaves listings unassigned, "
         "but it is useful as a monitor for unusual listings.")
    para("A fair question is why not simply rank listings by sales. A ranking shows who sells most, but not who is premium, who is cheap and "
         "slow, or who is about to run out. Clustering combines price, sales and stock in one view and yields groups that each need a different action. "
         "That is the difference between a league table and a segmentation.")
    ec = pd.DataFrame([
        ["Covers every listing", "Yes (0% noise)", "Yes (0% noise)", "No (8.9% noise, 90.7% in one group)"],
        ["Scores a new listing instantly", "Yes: nearest centre", "No: tree must be re-built", "Partly: needs the full data"],
        ["Stable week to week", "Yes (ARI 0.93)", "No (ARI 0.48)", "Moderate (ARI 0.75)"],
        ["Easy to explain to managers", "Yes: four typical profiles", "Medium: dendrogram", "Hard: noise and one big group"],
        ["Scales to millions of listings", "Yes", "Poor (memory grows with the square of listings)", "Medium"],
        ["Best role", "Main segmentation", "Cross-check", "Outlier alert"],
    ], columns=["E-commerce requirement", "K-Means", "Ward hierarchical", "DBSCAN"])
    table(ec, "Suitability of each model for an e-commerce catalogue.", None, [4.2, 3.6, 4.4, 4.8], font=8.5, key="table_ecom")
    heading("8. Recommendations for managers", 1)
    para("Each recommendation follows from the evidence in one segment ([[table_profiles]]):")
    bullets([
        "**Protect the best-sellers (Cluster 2).** They carry 92% of sales. Set automatic restock alerts when stock falls below 10 units "
        "and give these sellers priority in search and fulfilment.",
        "**Grow the premium segment (Cluster 0).** Demand is steady but slow. Bundle these listings with best-sellers on product pages and "
        "invest in better images and descriptions rather than discounts.",
        "**Rethink the budget segment (Cluster 1).** Low prices do not create sales without brand recognition. Stop paid promotion of unbranded "
        "items and move that budget to proven brands.",
        "**Fix the low-stock tail (Cluster 3).** Ask sellers to restock within 30 days, and delist listings that stay empty and unsold.",
        "**Operate the model.** Re-run the segmentation monthly, assign new listings to the nearest centre, and review DBSCAN’s noise points as unusual listings.",
    ])
    para("Start with the best-sellers and the low-stock tail, because they need the least effort and protect the most revenue. "
         "Measure success by stock-outs in Cluster 2, the share of Cluster 3 listings restocked or delisted within 30 days, "
         "and sales per advertising dollar in Cluster 1.")
    heading("9. Limitations", 1)
    para("The marketplace caps visible stock at 10, so stock above that is unknown. The data is one snapshot of one product family, so the segments may "
         "differ for other categories. The clusters describe association, not cause: a premium price does not by itself make a listing slow. "
         "Finally, the structure is a continuum, so listings near a boundary can fall in either group.")
    para("These limits do not change the main finding, but they set how the results should be used: as a guide for prioritising attention, "
         "reviewed monthly, with the stock cap and the narrow product range kept in mind.")
    heading("10. Conclusion and future work", 1)
    para("This project shows that a simple, well-prepared K-Means model can turn an unlabelled catalogue into four clear and actionable segments. "
         "My main lesson is that preparation mattered more than algorithm choice: recovering values from the listing text and handling the hidden stock cap "
         "changed the result more than any tuning. I also learned to treat a weak result honestly: DBSCAN’s poor fit taught us something real about the data.")
    para("To extend the work I would add real stock counts and revenue per listing, include text features from the descriptions, "
         "track segments over time to see which listings move between them, and test whether the segments predict future sales. "
         "I would also build a small dashboard so managers can see each listing’s segment.")


def references_and_appendix():
    global section_tag
    section_tag = "Intro"  # excluded from the counted totals below
    heading("References", 1)
    refs = [
        "Davies, D.L. and Bouldin, D.W. (1979) 'A cluster separation measure', *IEEE Transactions on Pattern Analysis and Machine Intelligence*, PAMI-1(2), pp. 224-227.",
        "Caliński, T. and Harabasz, J. (1974) 'A dendrite method for cluster analysis', *Communications in Statistics*, 3(1), pp. 1-27.",
        "Ester, M., Kriegel, H.-P., Sander, J. and Xu, X. (1996) 'A density-based algorithm for discovering clusters in large spatial databases with noise', in *Proceedings of the Second International Conference on Knowledge Discovery and Data Mining*. Portland: AAAI Press, pp. 226-231.",
        "Hubert, L. and Arabie, P. (1985) 'Comparing partitions', *Journal of Classification*, 2(1), pp. 193-218.",
        "MacQueen, J. (1967) 'Some methods for classification and analysis of multivariate observations', in *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability*. Berkeley: University of California Press, pp. 281-297.",
        "Müller, A.C. and Guido, S. (2016) *Introduction to machine learning with Python*. Sebastopol: O’Reilly Media.",
        "Pedregosa, F. et al. (2011) 'Scikit-learn: machine learning in Python', *Journal of Machine Learning Research*, 12, pp. 2825-2830.",
        "Pearson, K. (1901) 'On lines and planes of closest fit to systems of points in space', *Philosophical Magazine*, 2(11), pp. 559-572.",
        "Rousseeuw, P.J. (1987) 'Silhouettes: a graphical aid to the interpretation and validation of cluster analysis', *Journal of Computational and Applied Mathematics*, 20, pp. 53-65.",
        "Ward, J.H. (1963) 'Hierarchical grouping to optimize an objective function', *Journal of the American Statistical Association*, 58(301), pp. 236-244.",
    ]
    for r in refs:
        p = doc.add_paragraph(); add_runs(p, r); p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.first_line_indent = Cm(-0.6)
    doc.add_page_break()
    heading("Appendix A: Code, repository and reproducibility", 1)
    para("The full Task 1 code is in one Jupyter notebook that runs end to end (about 30 seconds) on Google Colab or locally. "
         "All materials are hosted in the GitHub repository below.", counted=False)
    for k, v in (("Repository", REPO),
                 ("Notebook (full code)", BASE + "COM7022_Clustering_25199053.ipynb"),
                 ("Data", BASE + "Sales-%5B5444%5D.csv"),
                 ("Figures", BASE + "output/figures"), ("Tables", BASE + "output/tables"),
                 ("Code screenshots", BASE + "output/screenshots"),
                 ("Interactive review page", "https://kvmmn.github.io/_COM7022_MachineLearning/")):
        p = doc.add_paragraph(); r = p.add_run(f"{k}: "); r.bold = True; p.add_run(v)
    para("Remaining code screenshots (clustering, hierarchical, DBSCAN and evaluation cells) appear in Sections 3 and 4. "
         "The notebook uses fixed random seeds (42), so every figure and table can be regenerated.", counted=False)
    p = doc.add_paragraph(); r = p.add_run("AI use declaration: ")
    r.bold = True
    p.add_run("AI tools were used to help structure and proofread this work. All analysis was run, checked and interpreted by me, "
              "and every number in this report was verified against the notebook output. (Edit to match the Arden AI policy.)")


def build():
    global doc, counted_words, section_tag, fig_n, tab_n, NEW_LABELS
    doc = Document()
    counted_words = {"Task 1": 0, "Task 2": 0, "Intro": 0}
    section_tag, fig_n, tab_n, NEW_LABELS = "Intro", 0, 0, {}
    setup()
    title_page()
    intro()
    task1_data_prep()
    task1_models()
    task1_eval()
    task1_profiles()
    task2()
    references_and_appendix()


def main():
    global LABELS
    build()                 # pass 1: collect figure/table numbers
    LABELS = dict(NEW_LABELS)
    build()                 # pass 2: resolve [[key]] cross-references
    total = counted_words["Intro"] + counted_words["Task 1"] + counted_words["Task 2"]
    summary = (f"{total:,} words of body prose (Introduction {counted_words['Intro']}, Task 1 {counted_words['Task 1']}, "
               f"Task 2 {counted_words['Task 2']}); captions, tables, code screenshots, references and appendix excluded")
    for p in doc.paragraphs:
        if "WORDCOUNT_PLACEHOLDER" in p.text:
            for r in p.runs:
                r.text = r.text.replace("WORDCOUNT_PLACEHOLDER", summary)
    doc.save(DOCX)
    print(summary)
    print("saved", DOCX)


if __name__ == "__main__":
    main()
