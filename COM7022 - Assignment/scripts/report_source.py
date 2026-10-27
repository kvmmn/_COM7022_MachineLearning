"""Shared source for the COM7022 report builders.

Parses _brain/REPORT.md into a list of blocks, defines the data tables, KPI cards and recommendation
cards, numbers figures/tables in order of appearance, resolves [[key]] cross-references and counts words.
Used by 02_build_review_html.py (GitHub Pages portal) and 04_build_report_docx.py (Word/PDF report).
"""
import re
from pathlib import Path

import pandas as pd

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
        ["Stable between refreshes", "Yes · ARI 0.93", "No · ARI 0.48", "Partly · 0.75", "Partly · 0.71", "Yes · ARI 0.93–0.97"],
        ["Scales to millions of listings", "Yes · linear", "No · quadratic", "Partly", "Partly", "No · context limit"],
        ["Explainable to managers", "Yes · four profiles", "Partly", "No · one group", "No · half noise", "Partly · black box"],
        ["Recommended role", "Production model", "Cross-check", "Anomaly flag", "Data-quality probe", "Check on k"],
    ], columns=["Requirement", "K-Means", "Ward", "DBSCAN", "HDBSCAN", "TabClustPFN"]),
        "Operational suitability of each model for an e-commerce platform.", None)
    return t


HIGHLIGHT = {"table_kscan": 2, "table_comparison": 0}   # row to emphasise (chosen k / chosen model)

KPIS = [
    ("Core revenue engine", "92.3%", "of units sold come from 24.3% of listings (Cluster 2)", True),
    ("Inventory risk", "31.3%", "of listings sit in the low-stock tail (Cluster 3)", False),
    ("Model stability", "0.932", "K-Means bootstrap ARI over 30 resamples", False),
    ("PCA variance", "78.7%", "retained by the first two components", False),
]

RECS = [
    ("c2", "Protect · Cluster 2", "Secure the revenue engine",
     "92.3% of units sold from 24.3% of listings.",
     "Automated restock alerts below 10 units, priority search placement and fulfilment SLAs for these sellers."),
    ("c0", "Grow · Cluster 0", "Monetise the premium tier",
     "Highest prices (median $68.99) with steady, slow demand.",
     "Bundle with best-sellers on product pages and invest in premium content rather than discounting."),
    ("c1", "Reposition · Cluster 1", "Stop subsidising weak demand",
     "Cheapest offers (median $18.99) yet only 1.8% of volume.",
     "End paid promotion of unbranded items and reallocate budget to proven brands."),
    ("c3", "Audit · Cluster 3", "Clean up the low-stock tail",
     "31.3% of listings, median stock of 3, 14.1% at 'Last One'.",
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


if __name__ == "__main__":
    b, l, t, c = load()
    print(len(b), "blocks;", len(l), "labels;", c)
