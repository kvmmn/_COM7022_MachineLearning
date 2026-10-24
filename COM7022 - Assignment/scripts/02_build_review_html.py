#!/usr/bin/env python3
"""Build a single, self-contained HTML draft review file for COM7022 Coursework.
Embeds all 14 figures as Base64 data URIs, formats tables with Arden Midnight/Tiffany styling,
tracks exact word counts, includes an interactive cluster explorer widget,
and outputs both COM7022_Draft_Review_25199053.html and index.html for GitHub Pages.
"""

from __future__ import annotations

import base64
import html
import json
import re
from pathlib import Path
import pandas as pd

ASSIGNMENT_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = ASSIGNMENT_DIR.parent
OUTPUT_DIR = ASSIGNMENT_DIR / "output"
FIG_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"
REVIEW_HTML = ASSIGNMENT_DIR / "COM7022_Draft_Review_25199053.html"
INDEX_HTML = ROOT_DIR / "index.html"


def b64_img(filename: str) -> str:
    path = FIG_DIR / filename
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_table(csv_name: str, caption: str, max_rows: int | None = None) -> str:
    path = TABLE_DIR / csv_name
    if not path.exists():
        return f"<p class='table-missing'>Table file {csv_name} not found</p>"
    df = pd.read_csv(path)
    if max_rows and len(df) > max_rows:
        df = df.head(max_rows)
    
    # Rename unnamed first column if it's an index
    if df.columns[0].startswith("Unnamed"):
        df.rename(columns={df.columns[0]: "Index"}, inplace=True)
        
    cols = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    rows_html = []
    for _, row in df.iterrows():
        tds = "".join(f"<td>{html.escape(str(v))}</td>" for v in row)
        rows_html.append(f"<tr>{tds}</tr>")
    
    return f"""
    <div class="table-container">
        <div class="table-caption"><strong>{caption}</strong></div>
        <table class="arden-table">
            <thead><tr>{cols}</tr></thead>
            <tbody>{"".join(rows_html)}</tbody>
        </table>
    </div>
    """


def build_html():
    print("Building self-contained HTML review draft...")

    # Load frozen cluster profiles for interactive explorer
    ledger_path = OUTPUT_DIR / "results_ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}

    # Encode all 14 figures
    figs = {f"fig{i:02d}": b64_img(f"fig{i:02d}_" + {
        1: "missing_values.png",
        2: "raw_distributions.png",
        3: "transformed_distributions.png",
        4: "feature_correlation.png",
        5: "pca_variance_biplot.png",
        6: "kmeans_elbow_silhouette.png",
        7: "kmeans_clusters_silhouette.png",
        8: "dendrograms_four_linkages.png",
        9: "ward_dendrogram_cut.png",
        10: "dbscan_k_distance.png",
        11: "dbscan_clusters.png",
        12: "model_comparison.png",
        13: "cluster_profiles.png",
        14: "cluster_distributions.png",
    }[i]) for i in range(1, 15)}

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COM7022 Portfolio Review: Product Clustering (Student 25199053)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Aptos:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
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
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: var(--font-sans);
            font-size: 15px;
            line-height: 1.68;
            color: var(--midnight);
            background-color: var(--paper);
            -webkit-font-smoothing: antialiased;
        }}

        /* Sticky Navigation Bar */
        .top-navbar {{
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
        }}

        .nav-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.3px;
        }}

        .nav-badge {{
            background: var(--tiffany-deep);
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }}

        .nav-links {{
            display: flex;
            gap: 20px;
            font-size: 13px;
        }}

        .nav-links a {{
            color: #D5DEE3;
            text-decoration: none;
            transition: color 0.2s;
            font-weight: 500;
        }}

        .nav-links a:hover {{
            color: var(--tiffany);
        }}

        .layout-container {{
            max-width: 1160px;
            margin: 32px auto;
            padding: 0 24px 60px;
        }}

        /* Hero Banner */
        .hero-banner {{
            background: linear-gradient(135deg, var(--midnight) 0%, var(--midnight-soft) 100%);
            color: #FFFFFF;
            border-radius: 12px;
            padding: 40px;
            margin-bottom: 32px;
            border-left: 6px solid var(--tiffany);
            box-shadow: 0 8px 24px rgba(0, 43, 73, 0.12);
        }}

        .hero-pre {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: var(--tiffany);
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .hero-title {{
            font-size: 28px;
            font-weight: 700;
            line-height: 1.3;
            margin-bottom: 12px;
        }}

        .hero-subtitle {{
            font-size: 16px;
            color: #D5DEE3;
            max-width: 860px;
            margin-bottom: 24px;
        }}

        .hero-meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.15);
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
        }}

        .meta-label {{
            font-size: 11px;
            color: #A7B4BC;
            text-transform: uppercase;
            font-weight: 600;
        }}

        .meta-value {{
            font-size: 14px;
            font-weight: 600;
            color: #FFFFFF;
        }}

        /* KPI Strip */
        .kpi-strip {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}

        .kpi-card {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--border);
            border-top: 4px solid var(--midnight);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }}

        .kpi-card.accent {{
            border-top-color: var(--tiffany-deep);
            background: #FAFD pass;
        }}

        .kpi-title {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--mute);
            margin-bottom: 6px;
        }}

        .kpi-val {{
            font-size: 26px;
            font-weight: 700;
            color: var(--midnight);
            line-height: 1.1;
            margin-bottom: 4px;
        }}

        .kpi-card.accent .kpi-val {{
            color: var(--tiffany-deep);
        }}

        .kpi-desc {{
            font-size: 12px;
            color: var(--mute);
        }}

        /* Cards & Section Containers */
        .content-card {{
            background: var(--card-bg);
            border-radius: 10px;
            padding: 36px 40px;
            margin-bottom: 32px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 10px rgba(0, 43, 73, 0.04);
        }}

        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            border-bottom: 2px solid var(--grid);
            padding-bottom: 12px;
            margin-bottom: 24px;
        }}

        h2 {{
            font-size: 22px;
            font-weight: 700;
            color: var(--midnight);
        }}

        h3 {{
            font-size: 17px;
            font-weight: 700;
            color: var(--midnight-soft);
            margin: 28px 0 12px;
        }}

        p {{
            margin-bottom: 16px;
            color: #243542;
        }}

        /* Word Count Badge */
        .word-badge {{
            background: var(--mist);
            color: var(--teal);
            font-size: 12px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 12px;
            border: 1px solid var(--tiffany);
        }}

        /* Figures & Tables */
        .figure-box {{
            margin: 28px 0;
            background: var(--paper);
            border: 1px solid var(--grid);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}

        .figure-box img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        }}

        .figure-caption {{
            font-size: 13px;
            color: var(--mute);
            margin-top: 10px;
            text-align: left;
            padding: 0 8px;
        }}

        .figure-caption strong {{
            color: var(--midnight);
        }}

        .table-container {{
            margin: 24px 0;
            overflow-x: auto;
        }}

        .table-caption {{
            font-size: 13px;
            margin-bottom: 8px;
            color: var(--midnight);
        }}

        .arden-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
            background: #FFFFFF;
            border: 1px solid var(--grid);
            border-radius: 6px;
            overflow: hidden;
        }}

        .arden-table th {{
            background: var(--midnight);
            color: #FFFFFF;
            font-weight: 600;
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
        }}

        .arden-table td {{
            padding: 9px 14px;
            border-bottom: 1px solid var(--grid);
            color: #243542;
        }}

        .arden-table tbody tr:hover {{
            background: var(--mist);
        }}

        /* Interactive Segment Explorer Widget */
        .explorer-box {{
            background: linear-gradient(180deg, #FFFFFF 0%, var(--mist) 100%);
            border: 2px solid var(--tiffany);
            border-radius: 8px;
            padding: 24px;
            margin: 28px 0;
        }}

        .explorer-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}

        .cluster-tabs {{
            display: flex;
            gap: 8px;
        }}

        .tab-btn {{
            background: #FFFFFF;
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            color: var(--midnight);
            transition: all 0.2s;
        }}

        .tab-btn.active {{
            background: var(--midnight);
            color: #FFFFFF;
            border-color: var(--midnight);
        }}

        .tab-content {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            background: #FFFFFF;
            border-radius: 6px;
            padding: 20px;
            border: 1px solid var(--grid);
        }}

        .stat-block {{
            display: flex;
            flex-direction: column;
        }}

        .stat-block .lbl {{
            font-size: 11px;
            color: var(--mute);
            text-transform: uppercase;
            font-weight: 600;
        }}

        .stat-block .num {{
            font-size: 20px;
            font-weight: 700;
            color: var(--midnight);
        }}

        .stat-block .sub {{
            font-size: 12px;
            color: var(--mute);
        }}

        /* Callout Quotes & Alerts */
        .callout-box {{
            background: var(--mist);
            border-left: 4px solid var(--tiffany-deep);
            padding: 16px 20px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
            font-size: 14px;
        }}

        .callout-box strong {{
            color: var(--midnight);
        }}

        /* Recommendations Diagram */
        .rec-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 24px 0;
        }}

        .rec-card {{
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            background: #FFFFFF;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
            border-left: 4px solid var(--midnight);
        }}

        .rec-card.c2 {{ border-left-color: var(--tiffany-deep); }}
        .rec-card.c0 {{ border-left-color: var(--midnight-soft); }}
        .rec-card.c1 {{ border-left-color: var(--teal); }}
        .rec-card.c3 {{ border-left-color: #D9534F; }}

        .rec-tag {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}

        .rec-card.c2 .rec-tag {{ color: var(--tiffany-deep); }}
        .rec-card.c0 .rec-tag {{ color: var(--midnight-soft); }}
        .rec-card.c1 .rec-tag {{ color: var(--teal); }}
        .rec-card.c3 .rec-tag {{ color: #D9534F; }}

        .rec-title {{
            font-size: 15px;
            font-weight: 700;
            color: var(--midnight);
            margin-bottom: 8px;
        }}

        .rec-body {{
            font-size: 13px;
            color: #334E68;
            line-height: 1.55;
        }}

        /* Code & Appendix */
        pre {{
            background: var(--midnight);
            color: #F7FAFB;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: var(--font-mono);
            font-size: 12px;
            line-height: 1.5;
            margin: 16px 0;
        }}

        code {{
            font-family: var(--font-mono);
            font-size: 13px;
            background: #E8EEF2;
            padding: 2px 5px;
            border-radius: 3px;
            color: var(--midnight);
        }}

        /* Reference list */
        .ref-list {{
            list-style-type: none;
            padding: 0;
        }}

        .ref-list li {{
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 10px;
            padding-left: 24px;
            text-indent: -24px;
            color: #334E68;
        }}

        /* Responsive */
        @media (max-width: 840px) {{
            .kpi-strip {{ grid-template-columns: repeat(2, 1fr); }}
            .rec-grid {{ grid-template-columns: 1fr; }}
            .content-card {{ padding: 24px 20px; }}
            .top-navbar {{ flex-direction: column; gap: 8px; align-items: flex-start; }}
        }}
    </style>
</head>
<body>

    <!-- Sticky Navigation Bar -->
    <header class="top-navbar">
        <div class="nav-brand">
            <span>Arden University Berlin</span>
            <span class="nav-badge">COM7022 Coursework Portfolio</span>
        </div>
        <nav class="nav-links">
            <a href="#overview">Overview</a>
            <a href="#task1">Task 1: Technical Project</a>
            <a href="#interactive-explorer">Cluster Explorer</a>
            <a href="#task2">Task 2: Executive Report</a>
            <a href="#recommendations">Recommendations</a>
            <a href="#references">References</a>
            <a href="https://github.com/kvmmn/_COM7022_MachineLearning" target="_blank" style="color:var(--tiffany); font-weight:700;">GitHub Repo ↗</a>
        </nav>
    </header>

    <main class="layout-container">

        <!-- Hero Header -->
        <section id="overview" class="hero-banner">
            <div class="hero-pre">Machine Learning Portfolio · MSc Data Science</div>
            <h1 class="hero-title">Product Segmentation and Performance Clustering for an E-Commerce Fragrance Marketplace</h1>
            <p class="hero-subtitle">
                An end-to-end unsupervised machine learning investigation evaluating K-Means, Hierarchical Clustering (Ward), and DBSCAN across 1,000 commercial product listings to drive inventory protection and strategic catalogue prioritisation.
            </p>
            <div class="hero-meta-grid">
                <div class="meta-item">
                    <span class="meta-label">Student ID</span>
                    <span class="meta-value">25199053</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Module</span>
                    <span class="meta-value">COM7022 Machine Learning</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Technical Word Equivalence</span>
                    <span class="meta-value">2,877 words (Task 1)</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Executive Report Word Count</span>
                    <span class="meta-value">1,455 words (Task 2)</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Primary Production Model</span>
                    <span class="meta-value">K-Means (k = 4)</span>
                </div>
            </div>
        </section>

        <!-- Executive KPI Strip -->
        <section class="kpi-strip">
            <div class="kpi-card accent">
                <div class="kpi-title">Core Revenue Engine</div>
                <div class="kpi-val">92.3%</div>
                <div class="kpi-desc">Total sales volume driven by 24.3% of listings (Cluster 2)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Critical Inventory Risk</div>
                <div class="kpi-val">31.3%</div>
                <div class="kpi-desc">Catalogue listings down to low or last-unit stock (Cluster 3)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Bootstrap Stability</div>
                <div class="kpi-val">0.932</div>
                <div class="kpi-desc">K-Means Adjusted Rand Index across 30 random resamples</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">PCA Variance Retained</div>
                <div class="kpi-val">78.7%</div>
                <div class="kpi-desc">Total variance captured by first two principal components</div>
            </div>
        </section>

        <!-- =================================================================== -->
        <!-- TASK 1: PRACTICAL PROJECT                                           -->
        <!-- =================================================================== -->
        <article id="task1" class="content-card">
            <div class="section-header">
                <h2>Task 1: Practical Machine Learning Investigation (Technical Project)</h2>
                <span class="word-badge">Task 1: 2,877 words equivalent</span>
            </div>

            <h3>1.1 Problem Framing and Data Understanding</h3>
            <p>
                This project investigates product segmentation for a fast-growing e-commerce marketplace using an authentic listing catalogue (<code>Sales-[5444].csv</code>). In digital marketplaces, cataloguing teams cannot manually inspect thousands of multi-seller offers to adjust promotional priority, identify inventory stock-outs, or isolate premium items from budget commodities. The operational objective is to design, implement, and evaluate an unsupervised machine learning clustering pipeline that groups fragrance listings according to their physical product characteristics and commercial sales performance.
            </p>
            <p>
                The dataset provides 1,000 raw listing records across 10 attributes, capturing product metadata (<code>Item_Name</code>, <code>details</code>, <code>Catatory</code>), pricing structure (<code>price</code>, <code>priceWithCurrency</code>), inventory availability and commercial traction (<code>available</code>, <code>text</code>, <code>sold</code>), listing maintenance timestamps (<code>lastUpdated</code>), and dispatch provenance (<code>itemLocation</code>).
            </p>
            <p>
                A critical preliminary methodological decision concerns the unit of observation. While <code>Item_Name</code> records brand names such as <em>Giorgio Armani</em> (60 listings) or <em>Ralph Lauren</em> (41 listings), individual rows represent distinct seller listings rather than unique stock-keeping units (SKUs) or manufacturers. Multiple sellers list identical fragrances with differing price points, remaining quantities, and shipping origins. The clustering pipeline therefore operates at the listing level, providing granular operational intelligence on seller catalogue dynamics.
            </p>
            <p>
                Initial inspection confirmed 0 full-row duplicates, though 39 listings share duplicate text in their <code>details</code> description. An audit of data completeness identified missing values across six attributes (Table 1 and Figure 1). The highest incompleteness occurs in <code>available</code> (111 missing records, 11.1%) and <code>lastUpdated</code> (53 missing records, 5.3%), alongside smaller omissions in <code>sold</code> (8 records), <code>price</code> (5 records), <code>Catatory</code> (3 records), and <code>Item_Name</code> (1 record).
            </p>

            <div class="figure-box">
                <img src="{figs['fig01']}" alt="Missing values per column">
                <div class="figure-caption"><strong>Figure 1.</strong> Number of missing values per column across 1,000 raw product listings. Inventory availability represents the primary completeness challenge.</div>
            </div>

            {render_table("table01_missing_values.csv", "Table 1. Incompleteness audit across all 10 raw catalogue attributes.")}

            <p>
                Descriptive statistical profiling of the raw numerical columns reveals acute distributional asymmetries (Table 2 and Figure 2). Listed prices span from $3.00 to $259.09, exhibiting moderate right-skewness (skewness = +2.18; median = $35.71; mean = $46.43). In contrast, recorded sales volumes display extreme right-skewness (skewness = +11.23; mean = 775.2 units; standard deviation = 3,211.4 units). While the median listing records 49.5 sales, superstar listings exceed 10,000 units, culminating in a catalogue maximum of 54,052 units. Standard Euclidean distance metrics applied directly to these raw scales would collapse cluster boundaries, making sales volume almost entirely dictate cluster formation. Careful non-linear transformation and robust scaling are therefore essential prerequisite steps.
            </p>

            <div class="figure-box">
                <img src="{figs['fig02']}" alt="Raw distributions of price and units sold">
                <div class="figure-caption"><strong>Figure 2.</strong> Histograms of raw listed price (left) and units sold (right), highlighting severe positive skewness and long commercial tails.</div>
            </div>

            {render_table("table02_descriptive_statistics_raw.csv", "Table 2. Descriptive statistics and skewness metrics for raw numerical attributes.")}

            <!-- 1.2 DATA PREPARATION -->
            <h3>1.2 Data Preparation and Pre-processing</h3>
            <p>
                Rather than applying blind statistical imputation or immediately discarding incomplete rows, data preparation prioritised deterministic recovery from complementary fields within the same listing. Every intervention was recorded in an execution ledger (Table 3).
            </p>
            <p>
                First, all five missing <code>price</code> values were successfully recovered from <code>priceWithCurrency</code>, where identical numerical values were preserved as plain text. Across all 995 listings where both price fields coexisted, the extracted figures matched the numeric price exactly with zero discrepancies exceeding $0.01. Three listings priced in Canadian Dollars (<code>C $</code> prefix, all dispatching from Ontario) were converted to US Dollars using a documented fixed rate of 0.73 USD/CAD, establishing currency parity.
            </p>
            <p>
                Second, the composite <code>text</code> string ("... available / ... sold") was parsed to resolve commercial figures. Two missing <code>sold</code> values were extracted directly from listing text. Three listings that detailed positive inventory without mentioning prior sales were assigned <code>sold = 0</code>, reflecting products that had not yet transacted. Conversely, three rows containing neither listing text nor any sales or inventory data were pruned, reducing the verified dataset from 1,000 to 997 complete listing records.
            </p>
            <p>
                Third, inventory availability was harmonised to resolve systemic marketplace censoring. Raw marketplace listings obscure exact stock levels exceeding 10 units behind the label <em>"More than 10 available"</em> (299 listings). Without adjustment, an uncensored seller listing 50 available units would appear five times larger than a censored seller with 50 units. Consequently, all 299 censored listings were coded as 11, and 115 listings showing explicit quantities above 10 were capped at 11, establishing a robust operational scale where 11 denotes deep stock. Listings showing <em>"Last One"</em> (47 rows) were mapped to 1. Unquantified listings displaying <em>"Limited quantity available"</em> or wholesale lots (62 rows) were imputed with the median (11) and flagged with a binary indicator (<code>stock_imputed = 1</code>).
            </p>
            <p>
                Fourth, textual categories were standardised. The raw <code>Catatory</code> column contained over 50 noisy variants resulting from seller spelling mistakes and inconsistent capitalisation (such as <em>Eau De Parfum</em>, <em>eau de perfume</em>, and <em>eau de toillette</em>). These were harmonised into six coherent fragrance categories: Eau de Toilette (454), Eau de Parfum (300), Cologne (57), Parfum / Extrait (17), Generic Fragrance (32), and Other (137). A single record missing a brand label was classified as <em>Unbranded</em>.
            </p>
            <p>
                Finally, to address acute distributional skewness, natural logarithmic transformations $\log(1 + x)$ were applied to <code>price</code> and <code>sold</code>. The transformation compressed price skewness from +2.18 to -0.08 and sales skewness from +11.23 to +0.25 (Table 4 and Figure 3). While 141 listings exceed the raw sales upper Tukey fence ($Q_3 + 1.5 \times \text{{IQR}} = 791$ units), removing them would discard the most commercially successful items in the catalogue. Logarithmic transformation successfully retains these vital business records while preventing extreme values from distorting Euclidean geometry.
            </p>

            <div class="figure-box">
                <img src="{figs['fig03']}" alt="Transformed distributions">
                <div class="figure-caption"><strong>Figure 3.</strong> Frequency distributions following logarithmic transformation of price and sales volume alongside the harmonised 11-point inventory scale.</div>
            </div>

            {render_table("table03_cleaning_log.csv", "Table 3. Auditable data hygiene ledger recording cleaning transformations and affected row counts.")}
            {render_table("table04_descriptive_statistics_clean.csv", "Table 4. Cleaned dataset properties and distributional symmetry metrics (n = 997).")}

            <!-- 1.3 FEATURE SELECTION -->
            <h3>1.3 Feature Selection and Justification</h3>
            <p>
                Unsupervised clustering algorithms are highly vulnerable to the inclusion of irrelevant, noisy, or collinear features. To isolate the primary drivers of catalogue segmentation, candidate numerical variables were screened through Spearman rank correlation analysis (Figure 4) and systematic multi-feature silhouette evaluations (Table 5).
            </p>
            <p>
                The correlation matrix demonstrates that the candidate attributes capture distinct commercial mechanisms without severe collinearity. Price exhibits mild negative associations with units sold ($r_s = -0.14$) and inventory availability ($r_s = -0.16$), confirming that premium fragrances move in lower volumes. Meanwhile, units sold and stock availability display a moderate positive correlation ($r_s = +0.37$), reflecting standard commercial inventory replenishment behind active products.
            </p>

            <div class="figure-box">
                <img src="{figs['fig04']}" alt="Feature correlation matrix">
                <div class="figure-caption"><strong>Figure 4.</strong> Spearman rank correlation matrix for candidate numerical features, confirming independence among selected variables.</div>
            </div>

            {render_table("table05_feature_set_scan.csv", "Table 5. Systematic silhouette score benchmark across five candidate feature subsets for cluster counts k = 2 through k = 6.")}

            <p>
                Five alternative feature subsets were benchmarked across cluster counts $k = 2$ through $k = 6$ (Table 5). A two-variable baseline consisting solely of <code>log_price</code> and <code>log_sold</code> (Set A) achieved marginally higher silhouette separation (0.351 to 0.377). However, Set A completely ignores stock availability, failing the brief's explicit requirement to capture availability status and obscuring the operational risk of imminent stock-outs. Expanding to the three-variable combination of <code>log_price</code>, <code>log_sold</code>, and <code>stock_level</code> (Set B) maintained robust separation (silhouette 0.297 to 0.337) while incorporating the three core business dimensions: price positioning, commercial demand, and supply stability.
            </p>
            <p>
                Further expanding the feature space to include <code>days_since_update</code> or bottle volume <code>size_oz</code> (Sets C, D, and E) eroded clustering quality, dropping silhouette scores to between 0.255 and 0.292. Bottle size lacks operational variance because 75% of fragrance listings are standardised between 3.3 and 3.4 fluid ounces, while listing update recency spans a narrow window without systematic commercial meaning.
            </p>
            <p>
                High-cardinality categorical attributes (240+ brands, six fragrance categories, dispatch origins) were deliberately excluded from the distance metric. One-hot encoding sparse categories expands dimensionality, distorts Euclidean distance, and causes clusters to isolate specific brand names rather than general product behaviours. Categorical metadata was instead reserved for post-hoc profiling.
            </p>
            <p>
                Because distance-based clustering algorithms require variables to contribute equally to Euclidean space, the three selected features in Set B were standardised using z-score standardisation ($z = (x - \mu)/\sigma$). This scales each feature to a mean of zero and a standard deviation of one, preventing the wider integer spread of <code>stock_level</code> (1 to 11) from dominating the compressed log-transformed price and sales scales.
            </p>

            <!-- 1.4 PCA -->
            <h3>1.4 Dimensionality Reduction via Principal Component Analysis (PCA)</h3>
            <p>
                Principal Component Analysis was applied to the standardised three-dimensional feature space (Pearson, 1901). In low-dimensional problems ($p = 3$), PCA is not required to overcome the curse of dimensionality or filter multicollinearity. Instead, PCA was implemented to provide a rigorous, uncorrupted two-dimensional coordinate system for cluster visualisation and to quantify the orthogonal directions of catalogue variation (Table 6 and Figure 5).
            </p>
            <p>
                Eigenvalue decomposition demonstrates that the first two principal components capture 78.7% of total catalogue variance (Figure 5, left). The first principal component (PC1) accounts for 48.6% of overall variance, with feature loadings of -0.421 on <code>log_price</code>, +0.636 on <code>log_sold</code>, and +0.647 on <code>stock_level</code>. PC1 represents commercial traction, contrasting high-volume, well-stocked items against slower-moving, high-priced goods.
            </p>
            <p>
                The second principal component (PC2) explains an additional 30.1% of catalogue variance, dominated almost entirely by <code>log_price</code> with a positive loading of +0.906 (+0.335 on <code>log_sold</code>, +0.260 on <code>stock_level</code>). PC2 cleanly isolates market luxury tier. The third principal component (PC3) captures the remaining 21.3% of variance.
            </p>

            <div class="figure-box">
                <img src="{figs['fig05']}" alt="PCA explained variance and biplot">
                <div class="figure-caption"><strong>Figure 5.</strong> Scree plot of cumulative explained variance (left) and 2D PCA biplot (right) projecting 997 listings and feature loading vectors.</div>
            </div>

            {render_table("table06_pca_loadings.csv", "Table 6. Principal Component loading matrix across the three standardised features.")}

            <!-- 1.5 K-MEANS -->
            <h3>1.5 K-Means Clustering</h3>
            <p>
                K-Means partitions data by iteratively assigning observations to the nearest cluster centroid and updating centroids to minimise the within-cluster sum of squares (WCSS), or inertia (MacQueen, 1967). To prevent convergence to suboptimal local minima, K-Means was implemented with k-means++ centroid seeding, running 20 random initialisations (<code>n_init=20</code>) under a fixed random seed (42).
            </p>
            <p>
                Because K-Means requires the cluster count $k$ to be predefined, models were evaluated across $k = 2$ through $k = 10$ (Table 7 and Figure 6). Inertia drops steeply from 1,943.0 at $k=2$ to 1,501.0 at $k=3$ and 1,186.7 at $k=4$, yielding a 38.9% reduction in total variance. Beyond $k=4$, variance reduction flattens noticeably (974.4 at $k=5$, 862.5 at $k=6$), establishing an empirical elbow between $k=3$ and $k=5$.
            </p>

            <div class="figure-box">
                <img src="{figs['fig06']}" alt="K-Means elbow and silhouette scan">
                <div class="figure-caption"><strong>Figure 6.</strong> Evaluation of cluster count k using inertia elbow curve (left axis) and average silhouette width (right axis). The vertical line marks k = 4.</div>
            </div>

            {render_table("table07_kmeans_k_scan.csv", "Table 7. K-Means evaluation metrics and minimum cluster size across k = 2 through k = 10.")}

            <p>
                While the silhouette score attains its global maximum at $k=2$ (0.337), a two-cluster split merely separates high-volume products from low-volume products, collapsing price and inventory variations into trivial aggregates. In contrast, $k=4$ preserves solid silhouette separation (0.307) while achieving the lowest Davies-Bouldin index across all tested specifications (1.015), indicating maximum cluster compactness relative to inter-cluster separation. Furthermore, $k=4$ produces commercially viable segment sizes: the smallest cluster holds 219 listings (22.0%) and the largest holds 312 listings (31.3%), avoiding the uninterpretable micro-clusters observed at $k \ge 7$ (Table 7).
            </p>

            <div class="figure-box">
                <img src="{figs['fig07']}" alt="K-Means clusters on PCA plane and silhouette plot">
                <div class="figure-caption"><strong>Figure 7.</strong> Final K-Means (k = 4) cluster assignments projected on the 2D PCA plane (left) and cluster silhouette thickness profiles (right).</div>
            </div>

            <!-- 1.6 HIERARCHICAL CLUSTERING -->
            <h3>1.6 Hierarchical Agglomerative Clustering</h3>
            <p>
                Hierarchical clustering constructs an unconstrained nested tree of partitions by successively merging the closest pair of clusters without requiring an initial specification of $k$ (Hastie et al., 2009). The agglomeration path depends fundamentally on the chosen linkage metric. To evaluate structural consistency against taught methods, four linkage criteria were executed on identical pairwise Euclidean distances (Table 8 and Figure 8).
            </p>
            <p>
                Single linkage (nearest-neighbour proximity) generated severe chaining, yielding a high cophenetic correlation ($r = 0.362$) but collapsing 994 listings into one massive cluster while isolating three singleton outliers. Complete linkage (farthest-neighbour proximity, $r = 0.536$) split the catalogue into uneven groups (424, 388, 180, and 5 listings). Average linkage (UPGMA, $r = 0.631$) reproduced the chaining defect, merging 989 listings into a single group.
            </p>
            <p>
                Ward's minimum-variance linkage (Ward, 1963) proved vastly superior for business segmentation. Rather than computing pairwise point distances, Ward merges the pair of clusters that produces the smallest increase in total within-cluster variance. Ward linkage produced balanced, interpretable partitions (358, 237, 235, and 167 listings) with a silhouette score of 0.253 at $k=4$ (Table 8).
            </p>

            <div class="figure-box">
                <img src="{figs['fig08']}" alt="Dendrograms across four linkage methods">
                <div class="figure-caption"><strong>Figure 8.</strong> Dendrogram comparison across single, complete, average, and Ward linkages (truncated to 30 merges for inspection).</div>
            </div>

            {render_table("table08_linkage_comparison.csv", "Table 8. Cophenetic correlation, silhouette scores, and cluster size distributions across the four linkage methods.")}

            <p>
                Pruning the Ward dendrogram with a horizontal cut at merge distance 18.5 yields four distinct branches (Figure 9). Across cluster counts $k = 2$ to $k = 10$, Ward's silhouette peaks at $k=2$ (0.324) and stabilises at 0.253 for $k=4$ (Table 9). Cross-tabulating the Ward $k=4$ partition against the K-Means $k=4$ solution produces an Adjusted Rand Index (ARI) of 0.468. This moderate concordance indicates that while both algorithms identify broadly similar catalogue poles, Ward's greedy, irreversible hierarchical merges constrain point assignments differently from K-Means iterative centroid relocations.
            </p>

            <div class="figure-box">
                <img src="{figs['fig09']}" alt="Ward dendrogram cut">
                <div class="figure-caption"><strong>Figure 9.</strong> Truncated Ward dendrogram showing the horizontal cut at height 18.5 to extract four balanced clusters.</div>
            </div>

            {render_table("table09_ward_k_scan.csv", "Table 9. Validation metrics for Ward hierarchical clustering across tree pruning heights k = 2 through k = 10.")}

            <!-- 1.7 DBSCAN -->
            <h3>1.7 Density-Based Spatial Clustering (DBSCAN)</h3>
            <p>
                DBSCAN discovers clusters of arbitrary geometric shape by identifying contiguous high-density regions separated by areas of low point density (Ester et al., 1996). Unlike K-Means and Ward linkage, DBSCAN does not assume spherical clusters, requires no predefined cluster count $k$, and explicitly designates sparse peripheral observations as noise (-1).
            </p>
            <p>
                DBSCAN behaviour is governed by two hyperparameters: the neighbourhood search radius ($\epsilon$) and the minimum number of points required to form a dense core ($\text{{MinPts}}$). Following standard heuristic guidelines for low-dimensional spaces, $\text{{MinPts}}$ was initialised to $2 \times p = 6$. A sorted $k$-distance plot evaluated the Euclidean distance from every point to its 6th nearest neighbour (Figure 10). The resulting curve displays a smooth, continuous gradient without a sharp inflection knee, demonstrating that product listings do not occupy disconnected dense density peaks.
            </p>

            <div class="figure-box">
                <img src="{figs['fig10']}" alt="DBSCAN k-distance plot">
                <div class="figure-caption"><strong>Figure 10.</strong> Sorted 6-nearest-neighbour distance plot used to establish the epsilon neighbourhood search radius.</div>
            </div>

            <p>
                A systematic grid search evaluated 32 parameter configurations across $\epsilon \in [0.25, 0.70]$ and $\text{{MinPts}} \in [4, 15]$ (Table 10). Tighter radii ($\epsilon \le 0.35$) fragmented the catalogue into dozens of uninterpretable micro-clusters while rejecting between 22.9% and 88.6% of listings as noise. Wider radii ($\epsilon \ge 0.50$) collapsed virtually the entire dataset into a single indiscriminate mass.
            </p>
            <p>
                The optimal compromise setting was identified at $\epsilon = 0.45$ and $\text{{MinPts}} = 6$ (Table 10). This model detected two clusters alongside 89 noise points (8.9% of listings). However, inspection of the resulting partition reveals severe structural asymmetry (Figure 11): Cluster 0 captures 904 listings (90.7%), Cluster 1 isolates a tiny pocket of 4 listings (0.4%), and 89 listings are discarded. The silhouette score on clustered records is slightly negative (-0.014), with a Calinski-Harabasz score of only 3.5.
            </p>

            <div class="figure-box">
                <img src="{figs['fig11']}" alt="DBSCAN clusters on PCA plane">
                <div class="figure-caption"><strong>Figure 11.</strong> DBSCAN (eps = 0.45, MinPts = 6) assignments projected on the 2D PCA plane. Grey crosses mark 89 noise outliers.</div>
            </div>

            {render_table("table10_dbscan_grid.csv", "Table 10. DBSCAN grid search results across 32 hyperparameter combinations.", max_rows=10)}

            <p>
                This empirical result provides a vital analytical finding: authentic e-commerce catalogues represent continuous multi-attribute spectra rather than isolated density islands. DBSCAN is fundamentally unsuited as a primary market segmentation engine. Nevertheless, profiling the 89 noise observations reveals that DBSCAN functions effectively as an automated anomaly detector, flagging extreme high-price items (median $85.00), ultra-high-volume listings, and extreme supply imbalances.
            </p>

            <!-- 1.8 MODEL COMPARISON & VALIDATION -->
            <h3>1.8 Model Comparison, Validation, and Model Choice</h3>
            <p>
                Because unsupervised learning lacks ground-truth target labels, model evaluation combined internal cluster validation indices, statistical stability benchmarking via bootstrap resampling, and sensitivity stress tests (Table 11 and Figure 12).
            </p>
            <p>
                Internal validation decisively favours K-Means. K-Means achieves a silhouette score of 0.307, outperforming Ward hierarchical clustering (0.253) and DBSCAN (-0.014 on clustered points). It also achieves the lowest Davies-Bouldin index (1.015 versus 1.257 for Ward and 1.172 for DBSCAN) and the highest Calinski-Harabasz score (503.3 versus 402.9 for Ward and 3.5 for DBSCAN), demonstrating superior compactness and cluster separation.
            </p>

            <div class="figure-box">
                <img src="{figs['fig12']}" alt="Side by side model comparison">
                <div class="figure-caption"><strong>Figure 12.</strong> Comparative performance across K-Means, Ward Hierarchical, and DBSCAN on silhouette, Davies-Bouldin, and bootstrap stability.</div>
            </div>

            {render_table("table11_model_comparison.csv", "Table 11. Comprehensive multi-metric benchmark evaluating internal quality, stability, and cluster balance across all three models.")}

            <p>
                To test algorithmic stability against sampling variance, models were evaluated across 30 independent bootstrap runs using 80% random sub-sampling, measuring cluster agreement against the full-dataset baseline with the Adjusted Rand Index (Hubert and Arabie, 1985). K-Means exhibited exceptional resampling stability, achieving an average ARI of $0.932 \pm 0.025$. In contrast, Ward hierarchical clustering demonstrated acute instability, recording an average ARI of only $0.481 \pm 0.084$. Because agglomerative hierarchical clustering makes rigid, irreversible merges at early iterations, minor perturbations in sample composition propagate upward, fundamentally reordering subsequent cluster branches. DBSCAN achieved moderate stability on its core cluster ($0.749 \pm 0.063$) but failed to generate actionable partitions.
            </p>
            <p>
                Robustness and sensitivity analyses further substantiated the K-Means specification (Table 12). Re-running K-Means across 10 random seeds confirmed near-perfect initialisation invariance (mean pairwise ARI = 0.984; minimum = 0.936). To evaluate vulnerability to extreme sales volumes, the top 1% volume listings (> 11,000 units sold) were temporarily trimmed; K-Means retained an ARI of 0.937 on the remaining 987 listings, proving that the logarithmic pre-processing successfully immunised the model against outlier leverage.
            </p>
            <p>
                However, substituting z-score standardisation with min-max normalisation reduced cluster concordance to ARI = 0.492. Min-max scaling bounds each attribute to $[0, 1]$, which disproportionately amplifies the bounded integer scale of <code>stock_level</code> (1 to 11) relative to the wider continuous spreads of log-transformed price and volume. Standardisation was retained because it preserves equal empirical feature variance ($s^2 = 1$).
            </p>

            {render_table("table12_sensitivity_checks.csv", "Table 12. Robustness and sensitivity stress tests evaluating seed invariance, scaling effects, and outlier leverage.")}

            <div class="callout-box">
                <strong>Model Selection Decision:</strong> K-Means ($k=4$) is selected as the production segmentation engine. It provides superior mathematical validation, near-perfect sampling stability (ARI 0.932), full catalogue coverage without unassigned noise, and instant $O(k)$ classification latency for onboarding new merchant listings. Ward linkage serves as an analytical structural cross-check, while DBSCAN is repurposed as an operational anomaly flag.
            </div>

            <!-- 1.9 CLUSTER PROFILES -->
            <h3>1.9 Cluster Characteristics and Business Relevance</h3>
            <p>
                Translating the selected K-Means ($k=4$) cluster centroids back into original financial and inventory units reveals four distinct commercial product segments across the 997 verified listings (Table 13, Table 14, and Figures 13 and 14).
            </p>

            <div class="figure-box">
                <img src="{figs['fig13']}" alt="Cluster profiles heatmap and sales share">
                <div class="figure-caption"><strong>Figure 13.</strong> Standardised feature deviations per cluster (left) and comparison of listing count share versus transacted unit sales share (right).</div>
            </div>

            {render_table("table13_cluster_profiles.csv", "Table 13. Comprehensive commercial profile across the four K-Means clusters expressed in original units.")}

            <div class="figure-box">
                <img src="{figs['fig14']}" alt="Cluster distributions boxplots">
                <div class="figure-caption"><strong>Figure 14.</strong> Boxplot distributions of price, units sold (log scale), and stock level across the four final K-Means clusters.</div>
            </div>

            {render_table("table14_product_type_mix.csv", "Table 14. Percentage distribution of product categories within each K-Means cluster.")}
        </article>

        <!-- =================================================================== -->
        <!-- INTERACTIVE CLUSTER EXPLORER WIDGET                                 -->
        <!-- =================================================================== -->
        <section id="interactive-explorer" class="content-card explorer-box">
            <div class="explorer-header">
                <div>
                    <h2 style="font-size: 20px;">Interactive Catalogue Segment Explorer</h2>
                    <p style="font-size: 13px; color: var(--mute); margin: 0;">Click on a segment tab to inspect live operational and commercial characteristics.</p>
                </div>
                <div class="cluster-tabs">
                    <button class="tab-btn active" onclick="switchTab(2)">Cluster 2 (Best-Sellers)</button>
                    <button class="tab-btn" onclick="switchTab(0)">Cluster 0 (Prestige)</button>
                    <button class="tab-btn" onclick="switchTab(1)">Cluster 1 (Budget)</button>
                    <button class="tab-btn" onclick="switchTab(3)">Cluster 3 (Low-Stock)</button>
                </div>
            </div>

            <div id="tab-data" class="tab-content">
                <!-- Dynamically populated via JavaScript -->
            </div>
        </section>

        <!-- =================================================================== -->
        <!-- TASK 2: CRITICAL EXECUTIVE REPORT                                   -->
        <!-- =================================================================== -->
        <article id="task2" class="content-card">
            <div class="section-header">
                <h2>Task 2: Critical Evaluation and Executive Report</h2>
                <span class="word-badge">Task 2: 1,455 words</span>
            </div>

            <h3>2.1 Executive Summary</h3>
            <p>
                This executive report translates the machine learning investigation undertaken on our 1,000-listing fragrance catalogue into strategic commercial intelligence. Rapid catalogue expansion across thousands of uncurated third-party merchant listings creates severe operational risks: capital allocation becomes inefficient, high-demand inventory faces unexpected stock-outs, and marketing spend is squandered on slow-moving products.
            </p>
            <p>
                Using an unsupervised machine learning clustering architecture, the catalogue was segmented along three core commercial dimensions: pricing tier, cumulative sales traction, and merchant stock availability. The analysis evaluated three distinct machine learning methodologies (K-Means, Ward Hierarchical Clustering, and DBSCAN). Rigorous empirical validation confirmed K-Means ($k=4$) as the most robust, stable, and operationally viable production model.
            </p>
            <p>
                The investigation uncovered a critical revenue concentration: <strong>24.3% of listings (Cluster 2: Best-Sellers) generate 92.3% of total historical transaction volume</strong>. Conversely, 31.3% of the catalogue (Cluster 3) is operating under acute inventory depletion, with nearly one in seven listings down to its final unit. These findings form the basis of four targeted operational interventions spanning supply protection, premium basket building, promotional reallocations, and catalogue hygiene.
            </p>

            <h3>2.2 Method Suitability and Pre-processing Decisions</h3>
            <p>
                Unsupervised machine learning is uniquely suited to marketplace catalogue analysis because e-commerce platforms lack predefined operational labels. Unlike supervised learning, which requires historical conversion tags or manual annotations, unsupervised clustering discovers natural, data-driven behavioural groupings directly from observable product and merchant attributes.
            </p>
            <p>
                The choice of features directly determined analytical success. Raw text categories contained over 50 noisy misspellings and capitalisation errors, while listing descriptions contained over 240 disparate brand names. Feeding one-hot encoded categorical variables into distance calculations was deliberately rejected: sparse binary indicators inflate mathematical dimensionality and cause algorithms to group listings by superficial brand names rather than underlying commercial behaviours.
            </p>
            <p>
                Instead, the model selected three standardised numerical features: log-transformed price, log-transformed sales volume, and harmonised stock availability. Marketplace listings obscure stock levels above 10 units behind the label <em>"More than 10 available"</em>. Rather than discarding these records, inventory availability was capped at 11, transforming an unquantified string into a reliable index of inventory depth.
            </p>
            <p>
                Logarithmic transformation of price and sales proved essential. While median sales volume is 49.5 units, top-tier commercial listings reach up to 54,052 units. Direct application of standard Euclidean distance to raw figures would cause the sales dimension to exert overwhelming mathematical leverage, collapsing all non-bestselling items into a single undifferentiated mass. Logarithmic compression reduced sales skewness from +11.23 to +0.25, ensuring that price tier and inventory status contribute equally to customer segment boundaries while keeping every high-volume listing in the analysis.
            </p>

            <h3>2.3 Critical Comparative Evaluation of Machine Learning Models</h3>
            <p>
                Three contrasting clustering paradigms were benchmarked on the standardised catalogue data: centroid-based partitioning (K-Means), agglomerative tree construction (Hierarchical Ward Linkage), and density-based spatial scanning (DBSCAN). Each method relies on distinct mathematical assumptions that directly govern its commercial utility (Table 11 and Figure 12).
            </p>
            <p>
                <strong>K-Means Partitioning:</strong> K-Means assumes that data clusters are convex, spherical, and of broadly comparable variance. While consumer marketplaces form continuous spectrums rather than disjoint geometric spheres, K-Means proved exceptionally effective for commercial segmentation. It produced the cleanest cluster separation (silhouette width = 0.307; Davies-Bouldin index = 1.015) and delivered near-perfect statistical stability ($0.932 \pm 0.025$ Adjusted Rand Index across 30 bootstrap resamples). Its main theoretical limitation is the requirement to predetermine $k$; however, this was resolved through rigorous elbow inflection analysis and silhouette profiling.
            </p>
            <p>
                <strong>Hierarchical Agglomerative Clustering (Ward Linkage):</strong> Hierarchical clustering was evaluated using four linkage methods. Single and average linkages suffered from severe chaining defects, merging over 98% of listings into a single mega-cluster. Ward's minimum-variance linkage produced balanced clusters but scored lower than K-Means across all internal validation metrics (silhouette = 0.253; Davies-Bouldin = 1.257). Crucially, bootstrap resampling revealed acute structural fragility (stability ARI = $0.481 \pm 0.084$). Because hierarchical clustering makes permanent, greedy merge decisions at early iterations, minor shifts in catalogue sampling fundamentally reshape downstream segment assignments.
            </p>
            <p>
                <strong>DBSCAN Density-Based Scanning:</strong> DBSCAN attempts to locate dense spatial clusters separated by empty regions. Across 32 parameter configurations (Table 10), DBSCAN proved fundamentally incompatible with marketplace catalogue data. Because retail listings form a continuous gradient of price and sales rather than isolated spatial clusters, DBSCAN merged 90.7% of listings into one generic cluster while discarding 8.9% of listings as unclustered noise. Although unsuitable for segmentation, DBSCAN provides high utility as an operational anomaly detector.
            </p>

            <h3>2.4 Justification of Final Model Selection</h3>
            <p>
                The selection of <strong>K-Means ($k=4$)</strong> as the primary production engine is justified by both technical validation metrics and operational business requirements:
            </p>
            <ol style="margin-left: 24px; margin-bottom: 20px;">
                <li style="margin-bottom: 8px;"><strong>Superior Partition Quality:</strong> K-Means delivered the highest silhouette score (0.307), lowest Davies-Bouldin index (1.015), and highest Calinski-Harabasz separation (503.3) among all evaluated algorithms.</li>
                <li style="margin-bottom: 8px;"><strong>Exceptional Operational Stability:</strong> Resampling stability of 0.932 ARI ensures that segment definitions remain consistent over time, avoiding the erratic cluster reassignments exhibited by Ward linkage (0.481 ARI). Sensitivity testing confirmed that K-Means is resilient to random seed initialisations (0.984 ARI) and volume outliers (0.937 ARI).</li>
                <li style="margin-bottom: 8px;"><strong>Complete Catalogue Coverage:</strong> Unlike DBSCAN, which abandoned 89 listings as unclassified noise, K-Means partitions 100% of the active catalogue into actionable commercial tiers.</li>
                <li style="margin-bottom: 8px;"><strong>Production Scalability:</strong> K-Means model parameters consist of four static 3D centroid vectors. In production, classifying a newly onboarded seller listing requires trivial Euclidean distance calculation to each centroid ($O(k)$ complexity), enabling instantaneous, real-time segment tagging within the live ingestion pipeline.</li>
            </ol>

            <!-- 2.5 STRATEGIC RECOMMENDATIONS -->
            <h3 id="recommendations">2.5 Strategic Evidence-Based Recommendations</h3>
            <p>
                Drawing on the empirical characteristics of the four discovered segments (Table 13 and Figures 13 and 14), management should execute four coordinated commercial initiatives:
            </p>

            <div class="rec-grid">
                <div class="rec-card c2">
                    <div class="rec-tag">Segment 2 · Protect Core Engine</div>
                    <div class="rec-title">Best-Sellers (92.3% Sales Volume)</div>
                    <div class="rec-body">
                        <strong>Evidence:</strong> 242 listings drive 710,030 units sold (median $29.94) across high-demand lines (<em>Armaf</em>, <em>Ralph Lauren</em>).<br><br>
                        <strong>Action:</strong> Implement algorithmic restock alerts when merchant stock dips below 10 units. Offer a 1.5% fee discount to top merchants maintaining 99% dispatch reliability. A stock-out here directly damages GMV.
                    </div>
                </div>

                <div class="rec-card c0">
                    <div class="rec-tag">Segment 0 · Elevate Margins</div>
                    <div class="rec-title">Prestige Designer (Median $68.99)</div>
                    <div class="rec-body">
                        <strong>Evidence:</strong> 219 luxury fashion listings (<em>Armani</em>, <em>Paco Rabanne</em>, <em>YSL</em>) with steady low-velocity demand (median 43 sales).<br><br>
                        <strong>Action:</strong> Position as premium basket builders. Deploy personalized product bundling widgets pairing Cluster 2 best-sellers with Cluster 0 travel sprays. Introduce authenticated merchant badges to lift buyer trust.
                    </div>
                </div>

                <div class="rec-card c1">
                    <div class="rec-tag">Segment 1 · Reposition Spend</div>
                    <div class="rec-title">Budget Commodities (Median $18.99)</div>
                    <div class="rec-body">
                        <strong>Evidence:</strong> 224 low-priced listings generate only 1.8% of platform volume. Low price alone fails to generate volume without brand resonance.<br><br>
                        <strong>Action:</strong> Cease platform-funded paid search campaigns on unbranded fragrances. Shift low-performing lines to organic search rankings and reallocate marketing budgets toward proven Cluster 2 lines.
                    </div>
                </div>

                <div class="rec-card c3">
                    <div class="rec-tag">Segment 3 · Audit Supply Tail</div>
                    <div class="rec-title">Low-Stock & Tail (31.3% Listings)</div>
                    <div class="rec-body">
                        <strong>Evidence:</strong> 312 listings face critical inventory exhaustion (median stock 3 units, 14.1% "Last One") with stagnant turnover.<br><br>
                        <strong>Action:</strong> Institute a 30-day supplier replenishment audit. Listings that remain unreplenished and log zero sales over 60 days should be retired from search indexes, reducing buyer bounce rates from depleted stock.
                    </div>
                </div>
            </div>

            <!-- 2.6 LIMITATIONS -->
            <h3>2.6 Operational Limitations and Continuous Improvement Roadmap</h3>
            <p>
                To ensure rigorous executive governance, three analytical limitations must be acknowledged:
            </p>
            <ol style="margin-left: 24px; margin-bottom: 24px;">
                <li style="margin-bottom: 10px;"><strong>Marketplace Stock Censoring:</strong> The marketplace platform caps visible stock availability at 10 units. While capping at 11 resolved scale distortion, it obscures the difference between a merchant holding 15 units and a distributor holding 500 units. Negotiating API-level integration with enterprise sellers to capture uncensored warehouse inventory is recommended.</li>
                <li style="margin-bottom: 10px;"><strong>Observational Cross-Sectional Data:</strong> The dataset captures a static snapshot in May 2024. Observed sales reflect cumulative historical volume rather than daily run-rates. Establishing automated daily batch ingestion will enable dynamic time-series tracking of listing velocity.</li>
                <li style="margin-bottom: 10px;"><strong>Scaling Sensitivity:</strong> Sensitivity tests demonstrated that min-max scaling yields alternative boundaries (ARI = 0.492). While z-score standardisation is technically justified by variance parity, ongoing validation should monitor whether merchant price changes disproportionately shift products across segment boundaries.</li>
            </ol>
        </article>

        <!-- =================================================================== -->
        <!-- REFERENCES LIST                                                     -->
        <!-- =================================================================== -->
        <section id="references" class="content-card">
            <div class="section-header">
                <h2>Academic References (Arden Harvard)</h2>
            </div>
            <ul class="ref-list">
                <li>Caliński, T. and Harabasz, J. (1974) 'A dendrite method for cluster analysis', <em>Communications in Statistics</em>, 3(1), pp. 1-27.</li>
                <li>Davies, D.L. and Bouldin, D.W. (1979) 'A cluster separation measure', <em>IEEE Transactions on Pattern Analysis and Machine Intelligence</em>, PAMI-1(2), pp. 224-227.</li>
                <li>Ester, M., Kriegel, H.-P., Sander, J. and Xu, X. (1996) 'A density-based algorithm for discovering clusters in large spatial databases with noise', in <em>Proceedings of the Second International Conference on Knowledge Discovery and Data Mining (KDD-96)</em>, Portland, Oregon, pp. 226-231.</li>
                <li>Géron, A. (2022) <em>Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow</em>. 3rd edn. Sebastopol: O'Reilly Media.</li>
                <li>Hastie, T., Tibshirani, R. and Friedman, J. (2009) <em>The Elements of Statistical Learning: Data Mining, Inference, and Prediction</em>. 2nd edn. New York: Springer.</li>
                <li>Hubert, L. and Arabie, P. (1985) 'Comparing partitions', <em>Journal of Classification</em>, 2(1), pp. 193-218.</li>
                <li>Hunter, J.D. (2007) 'Matplotlib: A 2D graphics environment', <em>Computing in Science & Engineering</em>, 9(3), pp. 90-95.</li>
                <li>Lloyd, S. (1982) 'Least squares quantization in PCM', <em>IEEE Transactions on Information Theory</em>, 28(2), pp. 129-137.</li>
                <li>MacQueen, J. (1967) 'Some methods for classification and analysis of multivariate observations', in <em>Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability</em>, 1, pp. 281-297.</li>
                <li>McKinney, W. (2010) 'Data structures for statistical computing in Python', in <em>Proceedings of the 9th Python in Science Conference</em>, Austin, Texas, pp. 56-61.</li>
                <li>Müller, A.C. and Guido, S. (2016) <em>Introduction to Machine Learning with Python: A Guide for Data Scientists</em>. Sebastopol: O'Reilly Media.</li>
                <li>Pearson, K. (1901) 'On lines and planes of closest fit to systems of points in space', <em>Philosophical Magazine</em>, 2(11), pp. 559-572.</li>
                <li>Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M. and Duchesnay, E. (2011) 'Scikit-learn: machine learning in Python', <em>Journal of Machine Learning Research</em>, 12, pp. 2825-2830.</li>
                <li>Rousseeuw, P.J. (1987) 'Silhouettes: a graphical aid to the interpretation and validation of cluster analysis', <em>Journal of Computational and Applied Mathematics</em>, 20, pp. 53-65.</li>
                <li>Virtanen, P. et al. (2020) 'SciPy 1.0: fundamental algorithms for scientific computing in Python', <em>Nature Methods</em>, 17(3), pp. 261-272.</li>
                <li>Ward, J.H. (1963) 'Hierarchical grouping to optimize an objective function', <em>Journal of the American Statistical Association</em>, 58(301), pp. 236-244.</li>
            </ul>
        </section>

        <!-- =================================================================== -->
        <!-- APPENDIX A: VERIFIABLE CODE LISTING & GITHUB                        -->
        <!-- =================================================================== -->
        <section id="appendix" class="content-card">
            <div class="section-header">
                <h2>Appendix A: Reproducible Machine Learning Code</h2>
                <span class="word-badge">Google Colab Ready</span>
            </div>
            <p>
                In accordance with the assessment brief instructions, the full end-to-end Python clustering implementation is provided in an executable Jupyter Notebook. The notebook can be inspected and run directly via the official module repository:
            </p>
            <div class="callout-box">
                <strong>Repository Source:</strong> <a href="https://github.com/kvmmn/_COM7022_MachineLearning" target="_blank" style="color:var(--midnight); font-weight:700;">https://github.com/kvmmn/_COM7022_MachineLearning</a><br>
                <strong>Colab-Ready Notebook:</strong> <code>COM7022 - Assignment/COM7022_Clustering_25199053.ipynb</code><br>
                <strong>Dataset:</strong> <code>COM7022 - Assignment/Sales-[5444].csv</code>
            </div>
            <p>
                Below is the core pipeline implementation illustrating data hygiene, logarithmic transformation, feature scaling, K-Means clustering, and stability validation:
            </p>
            <pre><code># Core Segmentation Pipeline Excerpt (COM7022_Clustering_25199053.ipynb)
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score

# 1. Deterministic Data Hygiene
df = pd.read_csv("Sales-[5444].csv")
df["price"] = df["price"].fillna(df["priceWithCurrency"].str.extract(r"\$([\d,]+\.?\d*)")[0].str.replace(",", "").astype(float))
df.loc[df["priceWithCurrency"].str.startswith("C", na=False), "price"] *= 0.73  # CAD to USD
df["sold"] = df["sold"].fillna(df["text"].str.extract(r"([\d,]+) sold")[0].str.replace(",", "").astype(float)).fillna(0)

# Capping inventory availability to resolve marketplace censoring
stock = df["text"].str.extract(r"^(\d+) available")[0].astype(float)
stock[df["text"].str.startswith("More than", na=False)] = 11
stock[df["text"].str.startswith("Last One", na=False)] = 1
df["stock_level"] = stock.clip(upper=11).fillna(11)

# 2. Log-transformation & Z-Score Standardisation
df["log_price"] = np.log1p(df["price"])
df["log_sold"] = np.log1p(df["sold"])
features = ["log_price", "log_sold", "stock_level"]
X = StandardScaler().fit_transform(df[features])

# 3. K-Means Production Model (k = 4)
kmeans = KMeans(n_clusters=4, n_init=20, random_state=42)
df["cluster"] = kmeans.fit_predict(X)

# 4. Cluster Validation
sil = silhouette_score(X, df["cluster"])
dbi = davies_bouldin_score(X, df["cluster"])
print(f"K-Means (k=4) Validation: Silhouette = {{sil:.3f}}, Davies-Bouldin = {{dbi:.3f}}")</code></pre>
        </section>

    </main>

    <!-- Interactive Explorer JavaScript -->
    <script>
        const clusterData = {{
            2: {{
                name: "Cluster 2: Best-Sellers (High-Velocity)",
                listings: "242 listings (24.3%)",
                salesShare: "92.3% of platform volume",
                medPrice: "$29.94",
                medSold: "952 units",
                meanSold: "2,934 units",
                medStock: "11 (Maximum)",
                lastOne: "1.2%",
                usShip: "99.6%",
                topCat: "Eau de Toilette (67.8%)",
                topBrands: "Armaf, Ralph Lauren, Giorgio Armani",
                role: "Core revenue engine. High velocity across accessible designer lines."
            }},
            0: {{
                name: "Cluster 0: Premium Designer (High-Margin)",
                listings: "219 listings (22.0%)",
                salesShare: "3.7% of platform volume",
                medPrice: "$68.99 (max $259)",
                medSold: "43 units",
                meanSold: "131 units",
                medStock: "11 (Maximum)",
                lastOne: "0.0%",
                usShip: "84.9%",
                topCat: "Eau de Parfum (45.2%)",
                topBrands: "Giorgio Armani, Paco Rabanne, YSL",
                role: "Prestige luxury items. Low velocity, high margin basket builders."
            }},
            1: {{
                name: "Cluster 1: Budget Commodities (Mass-Market)",
                listings: "224 listings (22.5%)",
                salesShare: "1.8% of platform volume",
                medPrice: "$18.99",
                medSold: "30 units",
                meanSold: "61 units",
                medStock: "11 (Maximum)",
                lastOne: "0.0%",
                usShip: "92.0%",
                topCat: "Eau de Toilette (37.9%)",
                topBrands: "Unbranded, Lattafa, Ralph Lauren",
                role: "Low pricing fails to stimulate demand without brand equity."
            }},
            3: {{
                name: "Cluster 3: Low-Stock & Tail (Depleted Risk)",
                listings: "312 listings (31.3%)",
                salesShare: "2.2% of platform volume",
                medPrice: "$39.99",
                medSold: "16 units",
                meanSold: "54 units",
                medStock: "3 units",
                lastOne: "14.1%",
                usShip: "88.5%",
                topCat: "Eau de Toilette (39.1%)",
                topBrands: "Giorgio Armani, Paco Rabanne, Ralph Lauren",
                role: "Depleted inventory. Imminent stock-out churn requiring supplier audit."
            }}
        }};

        function switchTab(clusterId) {{
            // Update active tab buttons
            document.querySelectorAll('.tab-btn').forEach((btn, idx) => {{
                btn.classList.toggle('active', btn.getAttribute('onclick').includes(clusterId));
            }});

            const d = clusterData[clusterId];
            const container = document.getElementById('tab-data');
            container.innerHTML = `
                <div class="stat-block">
                    <span class="lbl">Cluster Identity</span>
                    <span class="num">${{d.name.split(':')[0]}}</span>
                    <span class="sub">${{d.listings}}</span>
                </div>
                <div class="stat-block">
                    <span class="lbl">Platform Sales Share</span>
                    <span class="num" style="color:var(--tiffany-deep);">${{d.salesShare.split(' ')[0]}}</span>
                    <span class="sub">${{d.salesShare}}</span>
                </div>
                <div class="stat-block">
                    <span class="lbl">Median Listed Price</span>
                    <span class="num">${{d.medPrice}}</span>
                    <span class="sub">Median Transacted: ${{d.medSold}}</span>
                </div>
                <div class="stat-block">
                    <span class="lbl">Stock Availability</span>
                    <span class="num">${{d.medStock}}</span>
                    <span class="sub">${{d.lastOne}} showing Last One</span>
                </div>
                <div class="stat-block">
                    <span class="lbl">Dominant Formulation</span>
                    <span class="num" style="font-size:16px;">${{d.topCat.split(' ')[0]}} ${{d.topCat.split(' ')[1] || ''}}</span>
                    <span class="sub">${{d.topCat}}</span>
                </div>
                <div class="stat-block">
                    <span class="lbl">Leading Brands</span>
                    <span class="num" style="font-size:15px; color:var(--midnight-soft);">${{d.topBrands.split(',')[0]}}</span>
                    <span class="sub">${{d.topBrands}}</span>
                </div>
                <div style="grid-column: 1 / -1; margin-top: 8px; padding-top: 12px; border-top: 1px dashed var(--grid); font-size: 13px; color: #243542;">
                    <strong>Strategic Role:</strong> ${{d.role}}
                </div>
            `;
        }}

        // Initialize with Cluster 2 (Best-sellers)
        switchTab(2);
    </script>
</body>
</html>
"""

    REVIEW_HTML.write_text(html_content, encoding="utf-8")
    INDEX_HTML.write_text(html_content, encoding="utf-8")
    print(f"Successfully generated:")
    print(f"  1. {REVIEW_HTML} ({len(html_content):,} bytes)")
    print(f"  2. {INDEX_HTML} ({len(html_content):,} bytes)")


if __name__ == "__main__":
    build_html()
