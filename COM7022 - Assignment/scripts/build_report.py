#!/usr/bin/env python3
"""Build the COM7022 report and portal from the notebook outputs and the master text _brain/REPORT.md.

This is the ONLY script in the project. All analysis code, figures, tables and diagrams live in the Colab
notebook (COM7022_Clustering_25199053.ipynb); this file only assembles the deliverables from them:

  1. code screenshots     output/screenshots/   rendered from the notebook's own cells
  2. Word and PDF report  COM7022_Portfolio_25199053_final.docx / .pdf   (needs LibreOffice and pdftotext)
  3. GitHub Pages portal  index.html and COM7022_Draft_Review_25199053.html

Order of work: run the notebook (Colab or local), then
    python "COM7022 - Assignment/scripts/build_report.py"
Optional first argument: shots | docx | html, to run one step only.
"""
import base64
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import PythonLexer
from pygments.style import Style
from pygments.token import Comment, Keyword, Name, Number, Operator, String, Text


# ============================================================================================================
# 1. SHARED: master text, tables, KPI and recommendation cards, parser, word count
# ============================================================================================================

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
FIGS, SHOTS, TABLES = OUT / "figures", OUT / "screenshots", OUT / "tables"
SOURCE = ROOT / "_brain" / "REPORT.md"
NOTEBOOK = ROOT / "COM7022_Clustering_25199053.ipynb"

STUDENT_ID = "25199053"
REPO = "https://github.com/kvmmn/_COM7022_MachineLearning"
BLOB = REPO + "/blob/main/COM7022%20-%20Assignment/"
REPO_DIR = "COM7022 - Assignment/"
PAGES = "https://kvmmn.github.io/_COM7022_MachineLearning/"
TITLE = "Product Segmentation and Performance Clustering for an E-Commerce Fragrance Marketplace"
SUBTITLE = ("An end-to-end unsupervised machine learning investigation comparing K-Means, Ward hierarchical "
            "clustering, DBSCAN, HDBSCAN and the TabClustPFN foundation model across 1,000 marketplace listings, "
            "translated into evidence-based actions for catalogue strategy.")


def fmt(v):
    """Display value: integers without a trailing .0, other numbers as given."""
    if isinstance(v, float) and v.is_integer():
        return f"{int(v):,}" if abs(v) >= 10000 else str(int(v))
    if isinstance(v, str):
        try:
            f = float(v)
            if f.is_integer() and "." in v:
                return str(int(f))
        except ValueError:
            pass
    return str(v)


def repo_url(rel):
    return BLOB + rel.replace(" ", "%20").replace("[", "%5B").replace("]", "%5D")


# ----------------------------------------------------------------------------- tables
def _t(name, **kw):
    return pd.read_csv(TABLES / name, **kw)


def build_tables():
    t = {}
    mv = _t("table01_missing_values.csv")
    mv.columns = ["Attribute", "Missing", "Missing %"]
    t["table_missing"] = (mv[mv["Missing"] > 0], "Missing values per attribute in the raw extract (n = 1,000).",
                          "output/tables/table01_missing_values.csv")

    log = _t("table03_cleaning_log.csv", index_col=0)
    log.columns = ["Pre-processing step", "Rows affected", "Rationale"]
    t["table_cleaning"] = (log, "Execution log of every cleaning and transformation step.",
                           "output/tables/table03_cleaning_log.csv")

    d = _t("table04_descriptive_statistics_clean.csv", index_col=0)
    d = d.loc[["price", "sold", "stock_level", "log_price", "log_sold"], ["mean", "std", "min", "50%", "max", "skewness"]]
    d.insert(0, "Variable", ["price (US$)", "units sold", "stock level", "log price", "log units sold"])
    d.columns = ["Variable", "Mean", "Std", "Min", "Median", "Max", "Skewness"]
    t["table_clean_desc"] = (d, "Descriptive statistics of the 997 cleaned listings before and after the log transform.",
                             "output/tables/table04_descriptive_statistics_clean.csv")

    fs = _t("table05_feature_set_scan.csv")
    fs.columns = ["Feature set", "Features", "k = 2", "k = 3", "k = 4", "k = 5", "k = 6"]
    t["table_featuresets"] = (fs, "K-Means silhouette scores for five candidate feature sets (higher is better).",
                              "output/tables/table05_feature_set_scan.csv")

    t["table_techniques"] = (pd.DataFrame([
        ["K-Means", "Centroid-based: minimises within-cluster variance", "Fast, scalable, full coverage, interpretable centroids",
         "Requires k; assumes compact, similar-sized clusters"],
        ["Hierarchical (Ward)", "Agglomerative: merges clusters into a dendrogram", "No k needed upfront; reveals nested structure",
         "Irreversible merges; O(n²) memory; sensitive to sampling"],
        ["DBSCAN", "Density-based: grows clusters from dense regions", "Arbitrary shapes; explicit noise and outlier detection",
         "Needs density gaps; sensitive to ε and MinPts"],
        ["HDBSCAN", "Hierarchical density: keeps the most persistent clusters across all densities",
         "No ε; handles varying density; membership strengths", "Still needs density gaps; can leave many points as noise"],
        ["TabClustPFN", "Pre-trained transformer: clusters the table in context, no fitting",
         "Predicts k itself; no tuning; seconds to run", "Black box; external weights; small-data context limit"],
    ], columns=["Technique", "Principle", "Strengths", "Limitations"]),
        "Comparison of the clustering techniques applied.", None)

    pca = _t("table06_pca_loadings.csv")
    pca.columns = ["Feature", "PC1 (48.6%)", "PC2 (30.1%)", "PC3 (21.3%)"]
    t["table_pca"] = (pca, "PCA loadings of the standardised features.", "output/tables/table06_pca_loadings.csv")

    ks = _t("table07_kmeans_k_scan.csv")
    ks.columns = ["k", "Inertia", "Silhouette ↑", "Davies-Bouldin ↓", "Calinski-Harabasz ↑", "Smallest cluster"]
    t["table_kscan"] = (ks, "K-Means model scan for k = 2 to 10.", "output/tables/table07_kmeans_k_scan.csv")

    lk = _t("table08_linkage_comparison.csv")
    lk.columns = ["Linkage", "Cophenetic correlation", "Silhouette (k = 4)", "Cluster sizes"]
    t["table_linkage"] = (lk, "Comparison of four hierarchical linkage criteria.", "output/tables/table08_linkage_comparison.csv")

    t["table_metrics"] = (pd.DataFrame([
        ["Silhouette", "Cohesion vs separation of each listing (−1 to 1)", "Higher", "Favours convex clusters; ignores stability"],
        ["Davies-Bouldin", "Similarity of each cluster to its closest rival", "Lower", "Assumes centroid-shaped clusters"],
        ["Calinski-Harabasz", "Between- to within-cluster dispersion ratio", "Higher", "Inflated for convex clusters; weak for DBSCAN"],
        ["Bootstrap stability (ARI)", "Agreement of labels over 30 resamples of 80%", "Higher (max 1)", "Measures reproducibility, not quality"],
        ["Sensitivity (ARI)", "Agreement after changing seed, scaling or outliers", "Higher (max 1)", "Tests robustness to analyst choices"],
        ["Coverage and balance", "Share of noise; smallest and largest cluster", "Low noise, balanced", "Business usability rather than geometry"],
    ], columns=["Measure", "What it captures", "Better", "Caveat"]),
        "Evaluation framework: complementary measures and what each can and cannot tell us.", None)

    c = _t("table11_model_comparison.csv")
    c["stability"] = c["stability_ARI_mean"].map("{:.3f}".format) + " ± " + c["stability_ARI_sd"].map("{:.3f}".format)
    c = c[["model", "clusters", "noise_pct", "silhouette", "davies_bouldin", "calinski_harabasz", "stability",
           "smallest_cluster_pct", "largest_cluster_pct"]]
    c["model"] = c["model"].replace({"TabClustPFN (auto k)": "TCP (auto k)", "TabClustPFN (k = 4)": "TCP (k = 4)",
                                     "Hierarchical (Ward)": "Ward"})
    c.columns = ["Model", "Clusters", "Noise %", "Silhouette ↑", "DBI ↓", "CH ↑", "Stability ARI ↑", "Smallest %", "Largest %"]
    t["table_comparison"] = (c, "Comparative performance of the final models (density models scored on clustered listings only; TCP = TabClustPFN).", "output/tables/table11_model_comparison.csv")

    h = _t("table16_hdbscan_profile.csv")
    h.columns = ["HDBSCAN group", "Listings", "Median price (US$)", "Median units sold", "Median stock",
                 "At stock ceiling (%)"]
    t["table_hdbscan"] = (h, "HDBSCAN groups (min_cluster_size = 30, min_samples = 6) and their share of listings at the "
                          "censored stock ceiling.", "output/tables/table16_hdbscan_profile.csv")

    tc = _t("table17_tabclustpfn.csv")
    tc.columns = ["Variant", "Cluster", "Listings", "Median price (US$)", "Median units sold", "Units sold (%)",
                  "Median stock", "At stock ceiling (%)"]
    t["table_tabclustpfn"] = (tc, "TabClustPFN clusters with automatic k and with k fixed at 4.",
                              "output/tables/table17_tabclustpfn.csv")

    s = _t("table12_sensitivity_checks.csv")
    s.columns = ["Sensitivity test (K-Means, k = 4)", "ARI"]
    t["table_sensitivity"] = (s, "Robustness of the K-Means solution to analytical choices.",
                              "output/tables/table12_sensitivity_checks.csv")

    p = _t("table13_cluster_profiles.csv", index_col=0).T
    p = p.loc[["listings", "share_of_listings_pct", "median_price_usd", "median_units_sold", "share_of_units_sold_pct",
               "median_stock_level", "pct_last_one", "pct_ships_from_us", "top_product_type"]]
    p.insert(0, "Measure", ["Listings", "Share of listings (%)", "Median price (US$)", "Median units sold",
                            "Share of units sold (%)", "Median stock level", "Listings at 'Last One' (%)",
                            "Ships from US (%)", "Dominant product type"])
    p = p[["Measure", 2, 0, 1, 3]]
    p.columns = ["Measure", "C2 Best-Sellers", "C0 Premium", "C1 Budget", "C3 Low-Stock"]
    t["table_profiles"] = (p, "Business profile of the four K-Means segments.", "output/tables/table13_cluster_profiles.csv")

    t["table_ecom"] = (pd.DataFrame([
        ["Covers every listing", "Yes · 0% noise", "Yes · 0% noise", "No · 8.9% noise", "No · 47.0% noise", "Yes · 0% noise"],
        ["Scores new listings instantly", "Yes · nearest centroid", "No · rebuild tree", "Partly", "Partly", "Partly · re-run (~3 s)"],
        ["Stable between refreshes", "Yes · ARI 0.93", "No · ARI 0.48", "Partly · 0.75", "Partly · 0.75", "Yes · ARI 0.93–0.97"],
        ["Scales to millions of listings", "Yes · linear", "No · quadratic", "Partly", "Partly", "No · context limit"],
        ["Explainable to managers", "Yes · four profiles", "Partly", "No · one group", "No · half noise", "Partly · black box"],
        ["Recommended role", "Production model", "Cross-check", "Anomaly flag", "Data-quality probe", "Check on k"],
    ], columns=["Requirement", "K-Means", "Ward", "DBSCAN", "HDBSCAN", "TabClustPFN"]),
        "Operational suitability of each model for an e-commerce platform.", None)
    return t


HIGHLIGHT = {"table_kscan": 2, "table_comparison": 0}   # row to emphasise (chosen k / chosen model)

KPIS = [
    ("Core revenue engine", "90.7%", "of units sold come from 24.3% of listings (Cluster 2)", True),
    ("Inventory risk", "31.4%", "of listings sit in the low-stock tail (Cluster 3)", False),
    ("Model stability", "0.929", "K-Means bootstrap ARI over 30 resamples", False),
    ("PCA variance", "78.7%", "retained by the first two components", False),
]

RECS = [
    ("c2", "Protect · Cluster 2", "Secure the revenue engine",
     "90.7% of units sold from 24.3% of listings.",
     "Automated restock alerts below 10 units, priority search placement and fulfilment SLAs for these sellers."),
    ("c0", "Grow · Cluster 0", "Monetise the premium tier",
     "Highest prices (median $67.14) with steady, slow demand.",
     "Bundle with best-sellers on product pages and invest in premium content rather than discounting."),
    ("c1", "Reposition · Cluster 1", "Stop subsidising weak demand",
     "Cheapest offers (median $18.10) yet only 1.7% of volume.",
     "End paid promotion of unbranded items and reallocate budget to proven brands."),
    ("c3", "Audit · Cluster 3", "Clean up the low-stock tail",
     "31.4% of listings, median stock of 3, 14.7% at 'Last One'.",
     "30-day merchant restock notices; delist listings that remain empty and unsold after 60 days."),
]

SEGMENTS = {  # interactive explorer (values from table13)
    2: ("Best-Sellers", "Core revenue engine: high velocity across accessible designer lines."),
    0: ("Premium Designer", "Prestige tier: low velocity, high-value basket builders."),
    1: ("Budget Commodities", "Low price fails to create demand without brand equity."),
    3: ("Low-Stock Tail", "Depleted inventory with imminent stock-out and churn risk."),
}


# ----------------------------------------------------------------------------- parser
WORD = re.compile(r"[A-Za-z0-9£$%€][A-Za-z0-9'’.,£$%€/+\-=<>]*")


def words(text):
    text = re.sub(r"\[\[[a-z0-9_]+\]\]", "Figure 1", text)
    text = re.sub(r"[*`]", "", text)
    return len(WORD.findall(text))


def parse():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    blocks, bucket, i = [], "none", 0
    para = []

    def flush():
        if para:
            text = " ".join(x.strip() for x in para)
            blocks.append({"type": "para", "text": text, "bucket": bucket})
            para.clear()

    while i < len(lines):
        line = lines[i]
        m = re.match(r"<!--\s*count:(\w+)\s*-->", line.strip())
        if m:
            flush(); bucket = m.group(1); i += 1; continue
        if line.strip().startswith("<!--"):
            flush()
            while "-->" not in lines[i]:
                i += 1
            i += 1; continue
        if not line.strip():
            flush(); i += 1; continue
        if line.startswith("::: "):
            flush()
            body = line[4:].strip()
            kind, _, rest = body.partition(" ")
            if kind == "callout":
                text = []
                i += 1
                while lines[i].strip() != ":::":
                    text.append(lines[i].strip()); i += 1
                blocks.append({"type": "callout", "title": rest.strip(), "text": " ".join(text), "bucket": bucket})
            elif kind in ("figure", "shot"):
                stem, _, cap = rest.partition("|")
                blocks.append({"type": kind, "key": stem.strip(), "caption": cap.strip(), "bucket": bucket})
            elif kind == "part":
                tag, _, title = rest.partition("|")
                blocks.append({"type": "part", "tag": tag.strip(), "title": title.strip(), "bucket": bucket})
            elif kind == "table":
                blocks.append({"type": "table", "key": rest.strip(), "bucket": bucket})
            else:
                blocks.append({"type": kind, "bucket": bucket})
            i += 1; continue
        if line.startswith("$$"):
            flush()
            blocks.append({"type": "equation", "latex": line.strip().strip("$").strip(), "bucket": bucket})
            i += 1; continue
        m = re.match(r"^(#{1,3}) (.+?)(?:\s*\{#([\w-]+)\})?$", line)
        if m:
            flush()
            blocks.append({"type": f"h{len(m.group(1))}", "text": m.group(2), "id": m.group(3), "bucket": bucket})
            i += 1; continue
        if line.startswith("- "):
            flush()
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:].strip()); i += 1
            blocks.append({"type": "bullets", "items": items, "bucket": bucket})
            continue
        para.append(line); i += 1
    flush()
    return blocks


def number(blocks):
    """Figure/table labels in order of appearance."""
    labels, f, t = {}, 0, 0
    for b in blocks:
        if b["type"] in ("figure", "shot"):
            f += 1; b["label"] = f"Figure {f}"; labels[b["key"]] = b["label"]
        elif b["type"] == "table":
            t += 1; b["label"] = f"Table {t}"; labels[b["key"]] = b["label"]
    return labels


def resolve(text, labels):
    return re.sub(r"\[\[([a-z0-9_]+)\]\]", lambda m: labels.get(m.group(1), "??"), text)


def word_counts(blocks):
    c = {"intro": 0, "task1": 0, "task2": 0}
    for b in blocks:
        if b["bucket"] not in c:
            continue
        if b["type"] in ("para", "callout"):
            c[b["bucket"]] += words(b["text"])
        elif b["type"] == "bullets":
            c[b["bucket"]] += sum(words(x) for x in b["items"])
        elif b["type"] == "recs":
            c[b["bucket"]] += sum(words(" ".join(r[2:])) for r in RECS)
    c["task1_total"] = c["intro"] + c["task1"]
    c["total"] = c["task1_total"] + c["task2"]
    return c


def figure_path(b):
    if b["type"] == "shot":
        return SHOTS / f"{b['key']}.png", f"output/screenshots/{b['key']}.png"
    return FIGS / f"{b['key']}.png", f"output/figures/{b['key']}.png"


def load():
    blocks = parse()
    labels = number(blocks)
    for b in blocks:
        for k in ("text", "caption", "title"):
            if k in b:
                b[k] = resolve(b[k], labels)
        if "items" in b:
            b["items"] = [resolve(x, labels) for x in b["items"]]
    missing = [b["key"] for b in blocks if b["type"] in ("figure", "shot") and not figure_path(b)[0].exists()]
    assert not missing, f"missing images: {missing}"
    assert "??" not in str(blocks), "unresolved cross-reference"
    return blocks, labels, build_tables(), word_counts(blocks)


def appendix_cells():
    """(section heading, screenshot path, repo path) for every notebook code cell, in order."""
    import json
    nb = json.loads(NOTEBOOK.read_text())
    out, head, n = [], "Set-up", 0
    for cell in nb["cells"]:
        src = "".join(cell["source"]).strip()
        if cell["cell_type"] == "markdown" and src.startswith("## "):
            head = src.split("\n")[0][3:]
        elif cell["cell_type"] == "code":
            n += 1
            out.append((head, n, SHOTS / "appendix" / f"cell{n:02d}.png", f"output/screenshots/appendix/cell{n:02d}.png"))
    return out


# ============================================================================================================
# 2. CODE SCREENSHOTS (rendered from the notebook cells)
# ============================================================================================================

SHOT_DPI, SHOT_TEXT_WIDTH = 300, 6.6                 # code screenshots are drawn at the report's text width
FONT_REG = "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf"
SHOT = {"midnight": "#002B49", "soft": "#1A4A6B", "tiffany": "#66C9BA", "paper": "#F7FAFB", "grid": "#D5DEE3",
        "mute": "#5A6B75"}

# first line of the notebook cell -> (file stem, label shown in the header bar).
# Cells are found by content, so extra cells added by Colab (such as the "Open in Colab" badge) cannot shift them.
CELLS = {
    'DATA_FILE = "Sales-[5444].csv"': ("code01_import_data", "Data import"),
    "# Missing values per column, as counts and percentages": ("code02_missing_values", "Missing-value audit"),
    "df = raw.copy()": ("code03_price_recovery", "Cleaning: recover price"),
    "# 3.3 Units sold": ("code04_sold_recovery", "Cleaning: recover units sold"),
    "# 3.4 Stock level": ("code05_stock_level", "Cleaning: stock level and censoring"),
    "# 3.5 Product type": ("code06_product_type", "Cleaning: normalise product type"),
    "# 3.10 Transform the skewed": ("code07_log_transform", "Transformation: log(1 + x)"),
    'FEATURES = ["log_price", "log_sold", "stock_level"]': ("code08_scaling", "Scaling: StandardScaler"),
    "pca = PCA(random_state=SEED)": ("code09_pca", "PCA"),
    "k_values = range(2, 11)": ("code10_kmeans_scan", "K-Means: scan k"),
    "linkage_methods = [": ("code11_hierarchical", "Hierarchical: four linkages"),
    "MIN_SAMPLES = 2 * len(FEATURES)": ("code12_dbscan_kdist", "DBSCAN: k-distance"),
}


def find_cell(nb, first_line):
    hits = [c for c in nb["cells"] if c["cell_type"] == "code" and "".join(c["source"]).lstrip().startswith(first_line)]
    assert len(hits) == 1, (first_line, len(hits))
    return hits[0]


# ----------------------------------------------------------------------------- code screenshots
class ArdenCode(Style):
    """Print-friendly syntax colours in the report palette."""
    background_color = SHOT["paper"]
    default_style = ""
    styles = {
        Text: SHOT["midnight"], Comment: "italic " + SHOT["mute"], Keyword: "bold " + SHOT["midnight"],
        Name: SHOT["midnight"], Name.Function: "bold #2F6690", Name.Builtin: "#2F6690", String: "#1F8A7D",
        Number: "#C8553D", Operator: SHOT["soft"],
    }


def render_code(src, header, out):
    """Code at print size: 28 px mono at 300 dpi is about 6.7 pt, the same scale for every screenshot."""
    fmt = ImageFormatter(font_name="DejaVu Sans Mono", font_size=28, line_numbers=True, style=ArdenCode,
                         line_number_bg="#EDF1F4", line_number_fg="#8A9AA5", line_number_pad=10,
                         image_pad=22, line_pad=7)
    tmp = out.with_suffix(".tmp.png")
    tmp.write_bytes(highlight(src.rstrip() + "\n", PythonLexer(), fmt))
    body = Image.open(tmp).convert("RGB")
    tmp.unlink()
    max_w = int(SHOT_TEXT_WIDTH * SHOT_DPI)
    width = max_w                                            # every screenshot spans the full text width
    if body.width > max_w:                                   # very long lines: shrink to the text width
        body = body.resize((max_w, int(body.height * max_w / body.width)), Image.LANCZOS)
    bar_h = 62
    img = Image.new("RGB", (width, body.height + bar_h), SHOT["paper"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, bar_h], fill=SHOT["midnight"])
    d.rectangle([0, 0, 8, bar_h], fill=SHOT["tiffany"])
    f_reg, f_bold = ImageFont.truetype(FONT_REG, 28), ImageFont.truetype(FONT_BOLD, 29)
    name = "COM7022_Clustering_25199053.ipynb"
    d.text((26, 14), name, fill="#A9C4D4", font=f_reg)
    x = 26 + f_reg.getlength(name) + 18
    d.text((x, 14), "|", fill="#5F7F95", font=f_reg)
    d.text((x + 22, 13), header, fill="white", font=f_bold)
    gutter = Image.new("RGB", (width, body.height), SHOT["paper"])   # extend the code panel to the full width
    gutter.paste(body, (0, 0))
    img.paste(gutter, (0, bar_h))
    d.rectangle([0, 0, width - 1, img.height - 1], outline=SHOT["grid"], width=2)
    img.save(out, dpi=(SHOT_DPI, SHOT_DPI))


def build_code_screenshots():
    """One screenshot per key cell (report body) and one per code cell (Appendix A), rendered from the notebook."""
    SHOTS.mkdir(parents=True, exist_ok=True)
    (SHOTS / "appendix").mkdir(exist_ok=True)
    nb = json.loads(NOTEBOOK.read_text())
    for first_line, (stem, cap) in CELLS.items():
        render_code("".join(find_cell(nb, first_line)["source"]), cap, SHOTS / f"{stem}.png")
    n = 0
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            n += 1
            render_code("".join(cell["source"]), f"code cell {n}", SHOTS / "appendix" / f"cell{n:02d}.png")
    for old in (SHOTS / "appendix").glob("cell*.png"):          # drop screenshots of cells that no longer exist
        if int(old.stem[4:]) > n:
            old.unlink()
    print("built", len(CELLS), "body screenshots,", n, "appendix screenshots")


# ============================================================================================================
# 3. WORD AND PDF REPORT
# ============================================================================================================

DOCX = ROOT / "COM7022_Portfolio_25199053_final.docx"
PDF = DOCX.with_suffix(".pdf")
EQ_DIR = Path(tempfile.mkdtemp())

MIDNIGHT, MIDNIGHT_SOFT = RGBColor(0x00, 0x2B, 0x49), RGBColor(0x1A, 0x4A, 0x6B)
TIFFANY, TIFFANY_DEEP = RGBColor(0x66, 0xC9, 0xBA), RGBColor(0x3A, 0xA8, 0x9A)
TEAL, MUTE, INK, WHITE = RGBColor(0x0E, 0x7C, 0x8B), RGBColor(0x5A, 0x6B, 0x75), RGBColor(0x24, 0x35, 0x42), RGBColor(255, 255, 255)
HEX = {"midnight": "002B49", "soft": "1A4A6B", "tiffany": "66C9BA", "deep": "3AA89A", "teal": "0E7C8B",
       "mist": "E6F5F2", "paper": "F7FAFB", "grid": "D5DEE3", "red": "D9534F"}
FONT = "Calibri"


# ----------------------------------------------------------------------------- low-level helpers
def shade(cell, fill):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(sh)


def cell_borders(cell, **edges):
    """edges: top/left/bottom/right = (size in eighths of a point, hex colour); omitted edges get no border."""
    b = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        spec = edges.get(edge)
        if spec:
            el.set(qn("w:val"), "single"); el.set(qn("w:sz"), str(spec[0])); el.set(qn("w:color"), spec[1])
        else:
            el.set(qn("w:val"), "nil")
        b.append(el)
    cell._tc.get_or_add_tcPr().append(b)


def cell_margins(cell, top=80, bottom=80, left=120, right=120):
    m = OxmlElement("w:tcMar")
    for k, v in (("top", top), ("bottom", bottom), ("start", left), ("end", right)):
        el = OxmlElement(f"w:{k}"); el.set(qn("w:w"), str(v)); el.set(qn("w:type"), "dxa"); m.append(el)
    cell._tc.get_or_add_tcPr().append(m)


def table_no_borders(table):
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}"); el.set(qn("w:val"), "nil"); b.append(el)
    table._tbl.tblPr.append(b)


def keep_rows_together(table):
    for row in table.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def para_border_bottom(p, color, size=12, space=4):
    bdr = OxmlElement("w:pBdr")
    el = OxmlElement("w:bottom")
    el.set(qn("w:val"), "single"); el.set(qn("w:sz"), str(size)); el.set(qn("w:space"), str(space)); el.set(qn("w:color"), color)
    bdr.append(el)
    p._p.get_or_add_pPr().append(bdr)


def spacer(doc, after=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 0.8
    return p


def page_break(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_break(WD_BREAK.PAGE)


def hyperlink(p, url, text, size=8, color=TEAL, bold=False):
    r_id = p.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                            is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), str(color)); rPr.append(c)
    sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size * 2))); rPr.append(sz)
    if bold:
        rPr.append(OxmlElement("w:b"))
    r.append(rPr)
    t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r)
    p._p.append(h)


def run(p, text, size=None, bold=False, italic=False, color=None, font=None):
    r = p.add_run(text)
    if size:
        r.font.size = Pt(size)
    r.bold, r.italic = bold, italic
    if color is not None:
        r.font.color.rgb = color
    if font:
        r.font.name = font
    return r


def docx_inline(p, text, size=None, color=None):
    """Render **bold**, *italic*, `code` and bare URLs into runs."""
    for part in re.split(r"(\*\*.+?\*\*|(?<![*\w])\*(?!\s).+?(?<!\s)\*(?![*\w])|`[^`]+`|https?://\S+[^\s.,;:)])", text):
        if not part:
            continue
        if part.startswith("**"):
            run(p, part[2:-2], size, bold=True, color=color or MIDNIGHT)
        elif part.startswith("`"):
            run(p, part[1:-1], (size or 10.5) - 1, color=MIDNIGHT_SOFT, font="Consolas")
        elif part.startswith("http"):
            hyperlink(p, part, part, size=size or 10.5)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            run(p, part[1:-1], size, italic=True, color=color)
        else:
            run(p, part, size, color=color)


# ----------------------------------------------------------------------------- document set-up
def setup(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.1)
    sec.top_margin, sec.bottom_margin = Cm(1.9), Cm(1.8)
    st = doc.styles["Normal"]
    st.font.name, st.font.size, st.font.color.rgb = FONT, Pt(10.5), INK
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.paragraph_format.space_after, st.paragraph_format.line_spacing = Pt(6), 1.15
    for name, size, color, before, after in (("Heading 1", 18, MIDNIGHT, 4, 8), ("Heading 2", 12.5, MIDNIGHT_SOFT, 12, 4),
                                             ("Heading 3", 11, MIDNIGHT_SOFT, 8, 3)):
        h = doc.styles[name]
        h.font.name, h.font.size, h.font.bold, h.font.color.rgb = FONT, Pt(size), True, color
        rf = h.element.rPr.rFonts
        for att in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(att), FONT)
        for att in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            rf.attrib.pop(qn(att), None)
        h.paragraph_format.space_before, h.paragraph_format.space_after = Pt(before), Pt(after)
        h.paragraph_format.keep_with_next = True
    lb = doc.styles["List Bullet"]
    lb.font.name, lb.font.size = FONT, Pt(10.5)
    lb.paragraph_format.space_after = Pt(4)


def header_footer(section):
    section.different_first_page_header_footer = True
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run(hp, "COM7022 Machine Learning  ·  Product Segmentation Portfolio  ·  ", 8, color=MUTE)
    run(hp, f"Student ID {STUDENT_ID}", 8, bold=True, color=MIDNIGHT)
    para_border_bottom(hp, HEX["tiffany"], 6, 4)
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(fp, "Page ", 8.5, color=MUTE)
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        r = fp.add_run(); r.font.size = Pt(8.5); r.font.color.rgb = MUTE
        if kind:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = text
        r._r.append(el)


# ----------------------------------------------------------------------------- components
def band(doc, fill, rows, pad=(260, 260, 320, 320), left_bar=None):
    """Full-width coloured box. rows = [(text, size, bold, colour, space_after), ...]."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_no_borders(t)
    c = t.cell(0, 0); c.width = Cm(16.8)
    shade(c, fill); cell_margins(c, *pad)
    cell_borders(c, left=(40, left_bar)) if left_bar else None
    for i, (text, size, bold, color, after) in enumerate(rows):
        p = c.paragraphs[0] if i == 0 else c.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.05
        run(p, text, size, bold=bold, color=color)
    return t


def kpi_strip(doc):
    t = doc.add_table(rows=1, cols=4)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_no_borders(t)
    for i, (title, val, desc, acc) in enumerate(KPIS):
        c = t.cell(0, i); c.width = Cm(4.2)
        cell_borders(c, top=(30, HEX["deep"] if acc else HEX["midnight"]), left=(4, HEX["grid"]),
                     right=(4, HEX["grid"]), bottom=(4, HEX["grid"]))
        cell_margins(c, 140, 140, 140, 110)
        p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(2)
        run(p, title.upper(), 7.5, bold=True, color=MUTE)
        p = c.add_paragraph(); p.paragraph_format.space_after = Pt(1)
        run(p, val, 20, bold=True, color=TIFFANY_DEEP if acc else MIDNIGHT)
        p = c.add_paragraph(); p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
        run(p, desc, 8, color=MUTE)
    spacer(doc, 4)


def source_line(p, rel):
    run(p, "Source: ", 8, bold=True, color=TEAL)
    hyperlink(p, repo_url(rel), REPO_DIR + rel, 8)


def caption(doc, label, text, rel=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(3), Pt(12)
    run(p, f"{label}. ", 9, bold=True, color=MIDNIGHT)
    docx_inline(p, text, 9, MUTE)
    if rel:
        p.add_run("\n")
        source_line(p, rel)


def figure(doc, path, label, text, rel, max_height=22.0):
    """Insert at the image's native print size (all visuals are drawn at 300 dpi for a 16.8 cm text width),
    so type in every figure and screenshot appears at the size it was designed for."""
    w, h = Image.open(path).size
    width = min(16.8, w / 300 * 2.54, max_height * w / h)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(6), Pt(0)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width))
    caption(doc, label, text, rel)


def data_table(doc, df, label, cap, rel, hl=None, font=8.5):
    pc = doc.add_paragraph(); pc.paragraph_format.keep_with_next = True
    pc.paragraph_format.space_before, pc.paragraph_format.space_after = Pt(6), Pt(3)
    run(pc, f"{label}. ", 9, bold=True, color=MIDNIGHT); docx_inline(pc, cap, 9, MIDNIGHT)
    rows, cols = df.shape
    t = doc.add_table(rows=rows + 1, cols=cols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_no_borders(t)
    for j, col in enumerate(df.columns):
        c = t.cell(0, j); shade(c, HEX["midnight"]); cell_margins(c, 70, 70, 100, 80)
        p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
        run(p, str(col), font, bold=True, color=WHITE)
    for i in range(rows):
        for j in range(cols):
            c = t.cell(i + 1, j); cell_margins(c, 55, 55, 100, 80)
            cell_borders(c, bottom=(4, HEX["grid"]), left=(24, HEX["deep"]) if (i == hl and j == 0) else None)
            if i == hl:
                shade(c, HEX["mist"])
            elif i % 2:
                shade(c, HEX["paper"])
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            strong = j == 0 or i == hl
            run(p, fmt(df.iat[i, j]), font, bold=strong, color=MIDNIGHT if strong else INK)
    keep_rows_together(t)
    for row in t.rows[:-1]:
        for c in row.cells:
            c.paragraphs[0].paragraph_format.keep_with_next = True
    p = doc.add_paragraph(); p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(2), Pt(10)
    if rel:
        source_line(p, rel)


def callout(doc, title, text):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; table_no_borders(t)
    c = t.cell(0, 0); shade(c, HEX["mist"]); cell_borders(c, left=(40, HEX["deep"])); cell_margins(c, 170, 170, 240, 200)
    p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
    run(p, f"{title}: ", 10.5, bold=True, color=MIDNIGHT); docx_inline(p, text, 10.5)
    spacer(doc, 4)


def rec_cards(doc):
    colours = {"c2": HEX["deep"], "c0": HEX["soft"], "c1": HEX["teal"], "c3": HEX["red"]}
    t = doc.add_table(rows=2, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; table_no_borders(t)
    for k, (cls, tag, title, finding, action) in enumerate(RECS):
        c = t.cell(k // 2, k % 2); c.width = Cm(8.4)
        shade(c, "FFFFFF" if k in (0, 3) else HEX["paper"])
        cell_borders(c, left=(40, colours[cls]), top=(4, HEX["grid"]), right=(4, HEX["grid"]), bottom=(4, HEX["grid"]))
        cell_margins(c, 160, 160, 220, 160)
        col = RGBColor.from_string(colours[cls])
        p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(1); run(p, tag.upper(), 7.5, bold=True, color=col)
        p = c.add_paragraph(); p.paragraph_format.space_after = Pt(4); run(p, title, 11.5, bold=True, color=MIDNIGHT)
        p = c.add_paragraph(); p.paragraph_format.space_after = Pt(3)
        run(p, "Evidence: ", 9.5, bold=True, color=MIDNIGHT); docx_inline(p, finding, 9.5)
        p = c.add_paragraph(); p.paragraph_format.space_after = Pt(0)
        run(p, "Action: ", 9.5, bold=True, color=MIDNIGHT); docx_inline(p, action, 9.5)
    keep_rows_together(t)
    spacer(doc, 6)


def equation(doc, latex, n):
    tex = latex.replace(r"\lVert", r"\Vert").replace(r"\rVert", r"\Vert")
    path = EQ_DIR / f"eq{n}.png"
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${tex}$", fontsize=12, color="#002B49", math_fontfamily="dejavusans")
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    w, h = Image.open(path).size
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; table_no_borders(t)
    c = t.cell(0, 0); shade(c, HEX["paper"]); cell_margins(c, 140, 140, 200, 200)
    cell_borders(c, top=(4, HEX["grid"]), bottom=(4, HEX["grid"]), left=(4, HEX["grid"]), right=(4, HEX["grid"]))
    p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(path), height=Cm(h / 300 * 2.54))   # native size: 12 pt maths at 300 dpi
    spacer(doc, 4)


def part_banner(doc, tag, title, words):
    page_break(doc)
    band(doc, HEX["midnight"], [(tag.upper(), 9, True, TIFFANY, 2), (title, 20, True, WHITE, 3),
                                (f"{words:,} words of body text", 9, False, RGBColor(0xD5, 0xDE, 0xE3), 0)],
         pad=(300, 300, 340, 320), left_bar=HEX["tiffany"])
    spacer(doc, 6)


def h1(doc, text):
    p = doc.add_heading(text, level=1)
    para_border_bottom(p, HEX["tiffany"], 12, 4)


# ----------------------------------------------------------------------------- cover and contents
def cover(doc, wc):
    spacer(doc, 24)
    band(doc, HEX["midnight"], [
        ("MACHINE LEARNING PORTFOLIO  ·  MSC DATA SCIENCE  ·  ARDEN UNIVERSITY BERLIN", 8.5, True, TIFFANY, 12),
        (TITLE, 25, True, WHITE, 12),
        (SUBTITLE, 10.5, False, RGBColor(0xD5, 0xDE, 0xE3), 0)], pad=(620, 620, 480, 440), left_bar=HEX["tiffany"])
    spacer(doc, 10)
    meta = [("Student ID", STUDENT_ID), ("Module", "COM7022 Machine Learning · Assignment [5444]"),
            ("Assessment", "Portfolio · Task 1 Practical Project · Task 2 Critical Report"),
            ("Word count", f"{wc['total']:,} words of body text (Task 1: {wc['task1_total']:,} · Task 2: {wc['task2']:,}); "
                           "captions, tables, figures, code screenshots, references and appendix excluded"),
            ("Dataset", "Sales-[5444].csv · 1,000 listings × 10 attributes"),
            ("Repository", REPO), ("Review portal", PAGES)]
    t = doc.add_table(rows=len(meta), cols=2); table_no_borders(t); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (k, v) in enumerate(meta):
        a, b = t.cell(i, 0), t.cell(i, 1)
        a.width, b.width = Cm(3.4), Cm(13.4)
        for c in (a, b):
            cell_borders(c, bottom=(4, HEX["grid"])); cell_margins(c, 80, 80, 60, 60)
            c.paragraphs[0].paragraph_format.space_after = Pt(0)
        run(a.paragraphs[0], k.upper(), 8, bold=True, color=MUTE)
        if v.startswith("http"):
            hyperlink(b.paragraphs[0], v, v, 10, TEAL, True)
        else:
            run(b.paragraphs[0], v, 10, bold=(i == 0), color=MIDNIGHT)
    spacer(doc, 14)
    kpi_strip(doc)
    p = doc.add_paragraph()
    run(p, "Every figure, table and code screenshot carries a caption that names and links its exact file in the GitHub repository.",
        8.5, italic=True, color=MUTE)


def contents(doc, blocks, pages):
    page_break(doc)
    h1(doc, "Contents")
    t = doc.add_table(rows=0, cols=2); table_no_borders(t); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for b in blocks:
        if b["type"] == "part":
            cells = t.add_row().cells
            p = cells[0].paragraphs[0]; p.paragraph_format.space_before = Pt(10)
            run(p, f"{b['tag']}  ·  {b['title']}".upper(), 8.5, bold=True, color=TIFFANY_DEEP)
        elif b["type"] in ("h1", "h2"):
            lvl1 = b["type"] == "h1"
            cells = t.add_row().cells
            p = cells[0].paragraphs[0]
            p.paragraph_format.left_indent = Cm(0 if lvl1 else 0.7)
            p.paragraph_format.space_before = Pt(5 if lvl1 else 0)
            run(p, b["text"], 10.5 if lvl1 else 9.5, bold=lvl1, color=MIDNIGHT if lvl1 else INK)
            q = cells[1].paragraphs[0]; q.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            q.paragraph_format.space_before = Pt(5 if lvl1 else 0)
            run(q, str(pages.get(b["text"], "")), 10 if lvl1 else 9, bold=lvl1, color=MIDNIGHT)
            if lvl1:
                for c in cells:
                    cell_borders(c, bottom=(4, HEX["grid"]))
        else:
            continue
        for c, w in zip(cells, (15.2, 1.6)):
            c.width = Cm(w); cell_margins(c, 20, 20, 40, 40)
            c.paragraphs[0].paragraph_format.space_after = Pt(1)


# ----------------------------------------------------------------------------- build
def build_docx(pages):
    blocks, labels, tables, wc = load()
    doc = Document()
    setup(doc)
    header_footer(doc.sections[0])
    cover(doc, wc)
    contents(doc, blocks, pages)
    after_part, eq_n, section = False, 0, ""
    for b in blocks:
        t = b["type"]
        if t == "part":
            part_banner(doc, b["tag"], b["title"], wc["task1_total"] if "1" in b["tag"] else wc["task2"])
            after_part = True
        elif t == "h1":
            # sections flow on; only the back matter starts on a fresh page (parts have their own break)
            if b["text"].startswith(("References", "Appendix")):
                page_break(doc)
            elif not after_part:
                spacer(doc, 4)
            after_part = False
            section = b["text"]
            h1(doc, b["text"])
        elif t in ("h2", "h3"):
            doc.add_heading(b["text"], level=int(t[1]))
        elif t == "para":
            docx_inline(doc.add_paragraph(), b["text"])
        elif t == "bullets" and section == "References":
            for x in b["items"]:                  # Harvard list: hanging indent, no bullets
                p = doc.add_paragraph(); docx_inline(p, x, 9.5)
                p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Cm(0.8), Cm(-0.8)
        elif t == "bullets":
            for x in b["items"]:
                docx_inline(doc.add_paragraph(style="List Bullet"), x)
        elif t in ("figure", "shot"):
            path, rel = figure_path(b)
            text = ("Code screenshot: " + b["caption"]) if t == "shot" else b["caption"]
            figure(doc, path, b["label"], text, rel)
        elif t == "table":
            df, cap, rel = tables[b["key"]]
            data_table(doc, df, b["label"], cap, rel, HIGHLIGHT.get(b["key"]))
        elif t == "callout":
            callout(doc, b["title"], b["text"])
        elif t == "equation":
            eq_n += 1
            equation(doc, b["latex"], eq_n)
        elif t == "recs":
            rec_cards(doc)
        elif t == "kpis":
            kpi_strip(doc)
        elif t == "appendix":
            current = None
            for head, n, path, rel in appendix_cells():
                if head != current:
                    current = head
                    doc.add_heading(f"A · {head}", level=3)
                figure(doc, path, f"Code A{n}", f"Notebook code cell {n}", rel)
        # 'explorer' is interactive and portal-only; the same numbers are in the cluster profile table
    doc.save(DOCX)
    return blocks, wc


def to_pdf():
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(DOCX.parent), str(DOCX)],
                   check=True, capture_output=True)


def heading_pages(blocks):
    """PDF page of every h1/h2 heading, searched in order after the contents page."""
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True).stdout
    pages = text.split("\f")
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    found, start = {}, 2
    for b in blocks:
        if b["type"] in ("h1", "h2"):
            key = norm(b["text"])[:38]
            for i in range(start, len(pages)):
                if key in norm(pages[i]):
                    found[b["text"]] = i + 1
                    start = i
                    break
    return found


def build_docx_and_pdf():
    blocks, wc = build_docx({})
    to_pdf()
    pages = heading_pages(blocks)          # second pass writes real page numbers into the contents page
    build_docx(pages)
    to_pdf()
    final = heading_pages(blocks)
    if final != pages:
        build_docx(final); to_pdf()
    print("word count:", wc)
    print("saved", DOCX.name, "and", PDF.name)


# ============================================================================================================
# 4. GITHUB PAGES PORTAL
# ============================================================================================================

REVIEW_HTML = ROOT / "COM7022_Draft_Review_25199053.html"
INDEX_HTML = ROOT.parent / "index.html"

BASE_CSS = r"""
        :root {
            --midnight: #002B49;
            --midnight-soft: #1A4A6B;
            --tiffany: #66C9BA;
            --tiffany-deep: #3AA89A;
            --teal: #0E7C8B;
            --mist: #E6F5F2;
            --paper: #F7FAFB;
            --card-bg: #FFFFFF;
            --mute: #5A6B75;
            --grid: #D5DEE3;
            --border: #C9D5DD;
            --font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --font-mono: 'IBM Plex Mono', Menlo, Consolas, monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: var(--font-sans);
            font-size: 15px;
            line-height: 1.68;
            color: var(--midnight);
            background-color: var(--paper);
            -webkit-font-smoothing: antialiased;
        }

        /* Sticky Navigation Bar */
        .top-navbar {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(0, 43, 73, 0.96);
            backdrop-filter: blur(8px);
            border-bottom: 2px solid var(--tiffany);
            padding: 10px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #FFFFFF;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.3px;
        }

        .nav-badge {
            background: var(--tiffany-deep);
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .nav-links {
            display: flex;
            gap: 20px;
            font-size: 13px;
        }

        .nav-links a {
            color: #D5DEE3;
            text-decoration: none;
            transition: color 0.2s;
            font-weight: 500;
        }

        .nav-links a:hover {
            color: var(--tiffany);
        }

        .layout-container {
            max-width: 1160px;
            margin: 32px auto;
            padding: 0 24px 60px;
        }

        /* Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, var(--midnight) 0%, var(--midnight-soft) 100%);
            color: #FFFFFF;
            border-radius: 12px;
            padding: 40px;
            margin-bottom: 32px;
            border-left: 6px solid var(--tiffany);
            box-shadow: 0 8px 24px rgba(0, 43, 73, 0.12);
        }

        .hero-pre {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: var(--tiffany);
            font-weight: 600;
            margin-bottom: 8px;
        }

        .hero-title {
            font-size: 28px;
            font-weight: 700;
            line-height: 1.3;
            margin-bottom: 12px;
        }

        .hero-subtitle {
            font-size: 16px;
            color: #D5DEE3;
            max-width: 860px;
            margin-bottom: 24px;
        }

        .hero-meta-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.15);
        }

        .meta-item {
            display: flex;
            flex-direction: column;
        }

        .meta-label {
            font-size: 11px;
            color: #A7B4BC;
            text-transform: uppercase;
            font-weight: 600;
        }

        .meta-value {
            font-size: 14px;
            font-weight: 600;
            color: #FFFFFF;
        }

        /* KPI Strip */
        .kpi-strip {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }

        .kpi-card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--border);
            border-top: 4px solid var(--midnight);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }

        .kpi-card.accent {
            border-top-color: var(--tiffany-deep);
            background: #FBFEFD;
        }

        .kpi-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--mute);
            margin-bottom: 6px;
        }

        .kpi-val {
            font-size: 26px;
            font-weight: 700;
            color: var(--midnight);
            line-height: 1.1;
            margin-bottom: 4px;
        }

        .kpi-card.accent .kpi-val {
            color: var(--tiffany-deep);
        }

        .kpi-desc {
            font-size: 12px;
            color: var(--mute);
        }

        /* Cards & Section Containers */
        .content-card {
            background: var(--card-bg);
            border-radius: 10px;
            padding: 36px 40px;
            margin-bottom: 32px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 10px rgba(0, 43, 73, 0.04);
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            border-bottom: 2px solid var(--grid);
            padding-bottom: 12px;
            margin-bottom: 24px;
        }

        h2 {
            font-size: 22px;
            font-weight: 700;
            color: var(--midnight);
        }

        h3 {
            font-size: 17px;
            font-weight: 700;
            color: var(--midnight-soft);
            margin: 28px 0 12px;
        }

        p {
            margin-bottom: 16px;
            color: #243542;
        }

        /* Word Count Badge */
        .word-badge {
            background: var(--mist);
            color: var(--teal);
            font-size: 12px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 12px;
            border: 1px solid var(--tiffany);
        }

        /* Figures & Tables */
        .figure-box {
            margin: 28px 0;
            background: var(--paper);
            border: 1px solid var(--grid);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }

        .figure-box img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        }

        .figure-caption {
            font-size: 13px;
            color: var(--mute);
            margin-top: 10px;
            text-align: left;
            padding: 0 8px;
        }

        .figure-caption strong {
            color: var(--midnight);
        }

        .table-container {
            margin: 24px 0;
            overflow-x: auto;
        }

        .table-caption {
            font-size: 13px;
            margin-bottom: 8px;
            color: var(--midnight);
        }

        .arden-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
            background: #FFFFFF;
            border: 1px solid var(--grid);
            border-radius: 6px;
            overflow: hidden;
        }

        .arden-table th {
            background: var(--midnight);
            color: #FFFFFF;
            font-weight: 600;
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
        }

        .arden-table td {
            padding: 9px 14px;
            border-bottom: 1px solid var(--grid);
            color: #243542;
        }

        .arden-table tbody tr:hover {
            background: var(--mist);
        }

        /* Interactive Segment Explorer Widget */
        .explorer-box {
            background: linear-gradient(180deg, #FFFFFF 0%, var(--mist) 100%);
            border: 2px solid var(--tiffany);
            border-radius: 8px;
            padding: 24px;
            margin: 28px 0;
        }

        .explorer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .cluster-tabs {
            display: flex;
            gap: 8px;
        }

        .tab-btn {
            background: #FFFFFF;
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            color: var(--midnight);
            transition: all 0.2s;
        }

        .tab-btn.active {
            background: var(--midnight);
            color: #FFFFFF;
            border-color: var(--midnight);
        }

        .tab-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            background: #FFFFFF;
            border-radius: 6px;
            padding: 20px;
            border: 1px solid var(--grid);
        }

        .stat-block {
            display: flex;
            flex-direction: column;
        }

        .stat-block .lbl {
            font-size: 11px;
            color: var(--mute);
            text-transform: uppercase;
            font-weight: 600;
        }

        .stat-block .num {
            font-size: 20px;
            font-weight: 700;
            color: var(--midnight);
        }

        .stat-block .sub {
            font-size: 12px;
            color: var(--mute);
        }

        /* Callout Quotes & Alerts */
        .callout-box {
            background: var(--mist);
            border-left: 4px solid var(--tiffany-deep);
            padding: 16px 20px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
            font-size: 14px;
        }

        .callout-box strong {
            color: var(--midnight);
        }

        /* Recommendations Diagram */
        .rec-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 24px 0;
        }

        .rec-card {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            background: #FFFFFF;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
            border-left: 4px solid var(--midnight);
        }

        .rec-card.c2 { border-left-color: var(--tiffany-deep); }
        .rec-card.c0 { border-left-color: var(--midnight-soft); }
        .rec-card.c1 { border-left-color: var(--teal); }
        .rec-card.c3 { border-left-color: #D9534F; }

        .rec-tag {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .rec-card.c2 .rec-tag { color: var(--tiffany-deep); }
        .rec-card.c0 .rec-tag { color: var(--midnight-soft); }
        .rec-card.c1 .rec-tag { color: var(--teal); }
        .rec-card.c3 .rec-tag { color: #D9534F; }

        .rec-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--midnight);
            margin-bottom: 8px;
        }

        .rec-body {
            font-size: 13px;
            color: #334E68;
            line-height: 1.55;
        }

        /* Code & Appendix */
        pre {
            background: var(--midnight);
            color: #F7FAFB;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: var(--font-mono);
            font-size: 12px;
            line-height: 1.5;
            margin: 16px 0;
        }

        code {
            font-family: var(--font-mono);
            font-size: 13px;
            background: #E8EEF2;
            padding: 2px 5px;
            border-radius: 3px;
            color: var(--midnight);
        }

        /* Reference list */
        .ref-list {
            list-style-type: none;
            padding: 0;
        }

        .ref-list li {
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 10px;
            padding-left: 24px;
            text-indent: -24px;
            color: #334E68;
        }

        /* Responsive */
        @media (max-width: 840px) {
            .kpi-strip { grid-template-columns: repeat(2, 1fr); }
            .rec-grid { grid-template-columns: 1fr; }
            .content-card { padding: 24px 20px; }
            .top-navbar { flex-direction: column; gap: 8px; align-items: flex-start; }
        }
"""

EXTRA_CSS = r"""
        html { scroll-behavior: smooth; }
        section[id], article[id] { scroll-margin-top: 70px; }
        .progress { position: fixed; top: 0; left: 0; height: 3px; background: var(--tiffany); z-index: 1100; width: 0; }
        .nav-links { flex-wrap: wrap; gap: 16px; }
        .hero-banner { position: relative; overflow: hidden; }
        .hero-banner::after { content: ""; position: absolute; right: -80px; top: -80px; width: 320px; height: 320px;
            border-radius: 50%; background: radial-gradient(circle, rgba(102,201,186,0.25), rgba(102,201,186,0) 70%); }
        .hero-links { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 22px; }
        .hero-links a { color: #fff; text-decoration: none; font-size: 13px; font-weight: 600; padding: 7px 14px;
            border: 1px solid rgba(255,255,255,0.35); border-radius: 6px; }
        .hero-links a.primary { background: var(--tiffany-deep); border-color: var(--tiffany-deep); }
        .part-banner { display: flex; align-items: center; gap: 16px; margin: 48px 0 20px; }
        .part-banner .tag { background: var(--midnight); color: #fff; font-size: 12px; font-weight: 700; letter-spacing: 1px;
            text-transform: uppercase; padding: 6px 12px; border-radius: 4px; white-space: nowrap; }
        .part-banner .ttl { font-size: 20px; font-weight: 700; color: var(--midnight); }
        .part-banner .rule { flex: 1; height: 2px; background: linear-gradient(90deg, var(--tiffany), transparent); }
        .content-card ul.styled { margin: 0 0 18px 0; padding-left: 0; list-style: none; }
        .content-card ul.styled li { position: relative; padding-left: 22px; margin-bottom: 10px; color: #243542; }
        .content-card ul.styled li::before { content: ""; position: absolute; left: 4px; top: 10px; width: 8px; height: 8px;
            border-radius: 2px; background: var(--tiffany-deep); }
        .figure-box img { cursor: zoom-in; }
        .src-chip { display: inline-block; margin-top: 6px; font-size: 11.5px; font-family: var(--font-mono);
            color: var(--teal); background: var(--mist); border: 1px solid #CDEBE5; padding: 2px 8px; border-radius: 4px;
            text-decoration: none; word-break: break-all; }
        .src-chip:hover { background: #d8f0eb; }
        .table-caption strong { color: var(--midnight); }
        .arden-table td:first-child { font-weight: 600; color: var(--midnight); }
        details.code-shot { margin: 14px 0; border: 1px solid var(--grid); border-radius: 8px; background: #fff; overflow: hidden; }
        details.code-shot summary { cursor: pointer; list-style: none; padding: 11px 16px; font-size: 13.5px; font-weight: 600;
            color: var(--midnight); display: flex; align-items: center; gap: 10px; background: var(--paper); }
        details.code-shot summary::-webkit-details-marker { display: none; }
        details.code-shot summary .ico { font-family: var(--font-mono); font-size: 11px; background: var(--midnight); color: #fff;
            padding: 2px 7px; border-radius: 4px; }
        details.code-shot summary .chev { margin-left: auto; color: var(--mute); transition: transform .2s; }
        details.code-shot[open] summary .chev { transform: rotate(90deg); }
        details.code-shot .inner { padding: 14px 16px; border-top: 1px solid var(--grid); }
        details.code-shot img { max-width: 100%; border: 1px solid var(--grid); border-radius: 4px; }
        .code-group-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .8px;
            color: var(--mute); margin: 22px 0 6px; }
        .equation { margin: 18px 0; padding: 14px; background: var(--paper); border: 1px dashed var(--grid); border-radius: 8px;
            text-align: center; overflow-x: auto; }
        .rec-body p { margin: 0 0 6px; font-size: 13px; }
        .rec-body .lbl { font-weight: 700; color: var(--midnight); }
        .appendix-grid details summary { font-weight: 500; }
        .lightbox { position: fixed; inset: 0; background: rgba(0,20,35,.88); display: none; align-items: center;
            justify-content: center; z-index: 2000; padding: 24px; cursor: zoom-out; }
        .lightbox img { max-width: 96vw; max-height: 92vh; border-radius: 6px; background: #fff; }
        .lightbox.on { display: flex; }
        .site-footer { text-align: center; font-size: 12.5px; color: var(--mute); padding: 10px 0 40px; }
        .to-top { position: fixed; right: 20px; bottom: 20px; background: var(--midnight); color: #fff; width: 40px; height: 40px;
            border-radius: 50%; display: flex; align-items: center; justify-content: center; text-decoration: none;
            box-shadow: 0 4px 12px rgba(0,43,73,.25); font-size: 18px; }
        .arden-table tr.hl td { background: var(--mist); font-weight: 700; color: var(--midnight); }
        .arden-table tr.hl td:first-child { box-shadow: inset 4px 0 0 var(--tiffany-deep); }
        p a, .site-footer a { overflow-wrap: anywhere; }
        .explorer-header { flex-direction: column; align-items: flex-start; gap: 12px; }
        .cluster-tabs { flex-wrap: wrap; }
        @media (max-width: 840px) { .nav-links { display: none; } .nav-brand { flex-wrap: wrap; }
            .layout-container { padding: 0 14px 40px; } .hero-title { font-size: 22px; }
            .hero-meta-grid { grid-template-columns: 1fr 1fr; } .kpi-strip { grid-template-columns: 1fr 1fr; }
            .part-banner .rule { display: none; } }
        @media (max-width: 840px) { .part-banner { flex-wrap: wrap; } .hero-banner { padding: 28px 22px; } }
"""

NAV = [("overview", "Overview"), ("introduction", "Introduction"), ("data-preparation", "Data"),
       ("model-selection", "Models"), ("evaluation", "Evaluation"), ("clusters", "Segments"),
       ("executive-summary", "Executive Report"), ("recommendations", "Recommendations"), ("appendix", "Appendix")]


def b64(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def html_inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"(https?://[^\s<]+[^\s<.,;:)])", r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
    return t


def src_chip(rel):
    return (f'<a class="src-chip" href="{repo_url(rel)}" target="_blank" rel="noopener">'
            f"&#128193; {html.escape(REPO_DIR + rel)}</a>")


def render_table(df, label, caption, rel, hl=None):
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    rows = "".join(f'<tr{" class=hl" if i == hl else ""}>' + "".join(f"<td>{html.escape(fmt(v))}</td>" for v in r)
                   + "</tr>" for i, r in enumerate(df.astype(object).values))
    chip = f"<div>{src_chip(rel)}</div>" if rel else ""
    return (f'<div class="table-container"><div class="table-caption"><strong>{label}.</strong> {html.escape(caption)}</div>'
            f'<table class="arden-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>{chip}</div>')


def render_figure(b):
    path, rel = figure_path(b)
    img = f'<img src="{b64(path)}" alt="{html.escape(b["caption"])}" loading="lazy">'
    cap = f'<div class="figure-caption"><strong>{b["label"]}.</strong> {html_inline(b["caption"])}<br>{src_chip(rel)}</div>'
    if b["type"] == "shot":
        return (f'<details class="code-shot"><summary><span class="ico">&lt;/&gt;</span>{b["label"]} · Code: '
                f'{html_inline(b["caption"])}<span class="chev">&#9656;</span></summary><div class="inner">{img}{cap}</div></details>')
    return f'<div class="figure-box">{img}{cap}</div>'


def explorer():
    prof = pd.read_csv(TABLES / "table13_cluster_profiles.csv", index_col=0)
    js = []
    for c in (2, 0, 1, 3):
        r = prof.loc[c]
        name, role = SEGMENTS[c]
        js.append(f"""{c}: {{name: "Cluster {c}: {name}", listings: "{int(r.listings)} listings ({r.share_of_listings_pct}%)",
            share: "{r.share_of_units_sold_pct}%", medPrice: "${r.median_price_usd:.2f}", medSold: "{r.median_units_sold:g} units",
            meanSold: "{r.mean_units_sold:,.0f} units", medStock: "{r.median_stock_level:g}", lastOne: "{r.pct_last_one}%",
            us: "{r.pct_ships_from_us}%", cat: "{r.top_product_type}", brands: "{r.top_brands}", role: "{role}"}}""")
    tabs = "".join(f'<button class="tab-btn" data-c="{c}" onclick="switchTab({c})">Cluster {c} · {SEGMENTS[c][0]}</button>'
                   for c in (2, 0, 1, 3))
    return f"""
<section id="interactive-explorer" class="explorer-box">
  <div class="explorer-header"><div><h3 style="margin:0">Interactive Segment Explorer</h3>
  <p style="font-size:13px;color:var(--mute);margin:0">Select a segment to inspect its commercial profile.</p></div>
  <div class="cluster-tabs">{tabs}</div></div>
  <div id="tab-data" class="tab-content"></div>
</section>
<script>
const clusterData = {{{",".join(js)}}};
function switchTab(c) {{
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.c == c));
  const d = clusterData[c];
  document.getElementById('tab-data').innerHTML = `
    <div class="stat-block"><span class="lbl">Segment</span><span class="num">${{d.name.split(':')[0]}}</span><span class="sub">${{d.listings}}</span></div>
    <div class="stat-block"><span class="lbl">Share of units sold</span><span class="num" style="color:var(--tiffany-deep)">${{d.share}}</span><span class="sub">mean ${{d.meanSold}} per listing</span></div>
    <div class="stat-block"><span class="lbl">Median price</span><span class="num">${{d.medPrice}}</span><span class="sub">median sold: ${{d.medSold}}</span></div>
    <div class="stat-block"><span class="lbl">Median stock level</span><span class="num">${{d.medStock}}</span><span class="sub">${{d.lastOne}} at "Last One"</span></div>
    <div class="stat-block"><span class="lbl">Dominant product type</span><span class="num" style="font-size:16px">${{d.cat}}</span><span class="sub">${{d.us}} ship from the US</span></div>
    <div class="stat-block"><span class="lbl">Leading brands</span><span class="num" style="font-size:15px;color:var(--midnight-soft)">${{d.brands.split(',')[0]}}</span><span class="sub">${{d.brands}}</span></div>
    <div style="grid-column:1/-1;padding-top:12px;border-top:1px dashed var(--grid);font-size:13px"><strong>Strategic role:</strong> ${{d.role}}</div>`;
}}
switchTab(2);
</script>"""


def recs():
    cards = "".join(
        f'<div class="rec-card {cls}"><div class="rec-tag">{tag}</div><div class="rec-title">{title}</div>'
        f'<div class="rec-body"><p><span class="lbl">Evidence:</span> {html_inline(f)}</p><p><span class="lbl">Action:</span> {html_inline(a)}</p></div></div>'
        for cls, tag, title, f, a in RECS)
    return f'<div class="rec-grid">{cards}</div>'


def kpis():
    return '<section class="kpi-strip">' + "".join(
        f'<div class="kpi-card{" accent" if acc else ""}"><div class="kpi-title">{t}</div><div class="kpi-val">{v}</div>'
        f'<div class="kpi-desc">{d}</div></div>' for t, v, d, acc in KPIS) + "</section>"


def appendix(prefix):
    groups, out = {}, []
    for head, n, path, rel in appendix_cells():
        groups.setdefault(head, []).append((n, rel))
    for head, cells in groups.items():
        out.append(f'<div class="code-group-label">{html.escape(head)}</div>')
        for n, rel in cells:
            out.append(f'<details class="code-shot"><summary><span class="ico">cell {n:02d}</span>Notebook code cell {n}'
                       f'<span class="chev">&#9656;</span></summary><div class="inner">'
                       f'<img src="{prefix}{rel}" alt="Notebook code cell {n}" loading="lazy">'
                       f'<div class="figure-caption">{src_chip(rel)}</div></div></details>')
    return '<div class="appendix-grid">' + "".join(out) + "</div>"


def build_html(prefix):
    blocks, labels, tables, wc = load()
    parts, open_card, section = [], False, ""

    def close():
        nonlocal open_card
        if open_card:
            parts.append("</section>")
            open_card = False

    badges = {"intro": f"{wc['intro']:,} words", "task1": "Task 1", "task2": "Task 2", "none": ""}
    for b in blocks:
        t = b["type"]
        if t == "h1":
            section = b["text"]
            close()
            badge = badges.get(b["bucket"], "")
            parts.append(f'<section id="{b["id"]}" class="content-card"><div class="section-header"><h2>{html_inline(b["text"])}</h2>'
                         + (f'<span class="word-badge">{badge}</span>' if badge else "") + "</div>")
            open_card = True
        elif t == "part":
            close()
            words = wc["task1_total"] if "1" in b["tag"] else wc["task2"]
            parts.append(f'<div class="part-banner"><span class="tag">{b["tag"]}</span><span class="ttl">{b["title"]}</span>'
                         f'<span class="rule"></span><span class="word-badge">{words:,} words</span></div>')
        elif t in ("h2", "h3"):
            parts.append(f"<h3>{html_inline(b['text'])}</h3>")
        elif t == "para":
            parts.append(f"<p>{html_inline(b['text'])}</p>")
        elif t == "bullets" and section == "References":
            parts.append('<ul class="ref-list">' + "".join(f"<li>{html_inline(x)}</li>" for x in b["items"]) + "</ul>")
        elif t == "bullets":
            parts.append('<ul class="styled">' + "".join(f"<li>{html_inline(x)}</li>" for x in b["items"]) + "</ul>")
        elif t in ("figure", "shot"):
            parts.append(render_figure(b))
        elif t == "table":
            df, cap, rel = tables[b["key"]]
            parts.append(render_table(df, b["label"], cap, rel, HIGHLIGHT.get(b["key"])))
        elif t == "callout":
            parts.append(f'<div class="callout-box"><strong>{html_inline(b["title"])}:</strong> {html_inline(b["text"])}</div>')
        elif t == "equation":
            parts.append(f'<div class="equation">$${html.escape(b["latex"])}$$</div>')
        elif t == "explorer":
            parts.append(explorer())
        elif t == "recs":
            parts.append(recs())
        elif t == "kpis":
            parts.append(kpis())
        elif t == "appendix":
            parts.append(appendix(prefix))
    close()

    nav = "".join(f'<a href="#{i}">{n}</a>' for i, n in NAV)
    hero = f"""
<section id="overview" class="hero-banner">
  <div class="hero-pre">Machine Learning Portfolio · MSc Data Science · Arden University Berlin</div>
  <h1 class="hero-title">{TITLE}</h1>
  <p class="hero-subtitle">{SUBTITLE}</p>
  <div class="hero-meta-grid">
    <div class="meta-item"><span class="meta-label">Student ID</span><span class="meta-value">{STUDENT_ID}</span></div>
    <div class="meta-item"><span class="meta-label">Module</span><span class="meta-value">COM7022 Machine Learning</span></div>
    <div class="meta-item"><span class="meta-label">Task 1 · Practical project</span><span class="meta-value">{wc['task1_total']:,} words</span></div>
    <div class="meta-item"><span class="meta-label">Task 2 · Critical report</span><span class="meta-value">{wc['task2']:,} words</span></div>
    <div class="meta-item"><span class="meta-label">Production model</span><span class="meta-value">K-Means (k = 4)</span></div>
  </div>
  <div class="hero-links">
    <a class="primary" href="{REPO}" target="_blank" rel="noopener">GitHub repository ↗</a>
    <a href="{repo_url('COM7022_Clustering_25199053.ipynb')}" target="_blank" rel="noopener">Notebook ↗</a>
    <a href="{repo_url('COM7022_Portfolio_25199053_final.pdf')}" target="_blank" rel="noopener">Report (PDF) ↗</a>
  </div>
</section>"""
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COM7022 Portfolio · Product Clustering · {STUDENT_ID}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}}]}})"></script>
<style>{BASE_CSS}{EXTRA_CSS}</style>
</head>
<body>
<div class="progress" id="progress"></div>
<header class="top-navbar">
  <div class="nav-brand"><span>Arden University Berlin</span><span class="nav-badge">COM7022 Portfolio · {STUDENT_ID}</span></div>
  <nav class="nav-links">{nav}<a href="{REPO}" target="_blank" rel="noopener" style="color:var(--tiffany);font-weight:700">GitHub ↗</a></nav>
</header>
<main class="layout-container">
{hero}
{kpis()}
{''.join(parts)}
<div class="site-footer">COM7022 Machine Learning · Student ID {STUDENT_ID} · All figures, tables and code are reproducible from
<a href="{REPO}" target="_blank" rel="noopener">{REPO}</a></div>
</main>
<div class="lightbox" id="lightbox" onclick="this.classList.remove('on')"><img id="lightbox-img" alt=""></div>
<a class="to-top" href="#overview" aria-label="Back to top">&#8593;</a>
<script>
document.querySelectorAll('.figure-box img').forEach(img => img.addEventListener('click', () => {{
  document.getElementById('lightbox-img').src = img.src; document.getElementById('lightbox').classList.add('on'); }}));
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') document.getElementById('lightbox').classList.remove('on'); }});
window.addEventListener('scroll', () => {{
  const h = document.documentElement; document.getElementById('progress').style.width =
  (h.scrollTop / (h.scrollHeight - h.clientHeight) * 100) + '%'; }});
</script>
</body>
</html>
"""
    return page, wc


def build_html_portal():
    for path, prefix in ((REVIEW_HTML, ""), (INDEX_HTML, "COM7022%20-%20Assignment/")):
        page, wc = build_html(prefix)
        path.write_text(page, encoding="utf-8")
        print(f"wrote {path.name}: {len(page) / 1e6:.1f} MB")
    print("word count:", wc)


def main():
    steps = {"shots": build_code_screenshots, "docx": build_docx_and_pdf, "html": build_html_portal}
    chosen = sys.argv[1:] or list(steps)
    for name in chosen:
        steps[name]()


if __name__ == "__main__":
    main()
