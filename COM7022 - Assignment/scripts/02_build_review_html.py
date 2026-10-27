#!/usr/bin/env python3
"""Build the COM7022 GitHub Pages portal from the master report source (_brain/REPORT.md).

Keeps the original portal design (sticky navbar, hero banner, KPI strip, content cards, cluster explorer,
recommendation cards) and adds part banners, rendered equations (KaTeX), collapsible code screenshots,
figure lightbox and a repository link under every figure and table.
Writes COM7022_Draft_Review_25199053.html (assignment folder) and index.html (repo root).
Run:  python "COM7022 - Assignment/scripts/02_build_review_html.py"
"""
import base64
import html
import re

import pandas as pd

import report_source as rs

REVIEW_HTML = rs.ROOT / "COM7022_Draft_Review_25199053.html"
INDEX_HTML = rs.ROOT.parent / "index.html"

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


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"(https?://[^\s<]+[^\s<.,;:)])", r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
    return t


def src_chip(rel):
    return (f'<a class="src-chip" href="{rs.repo_url(rel)}" target="_blank" rel="noopener">'
            f"&#128193; {html.escape(rs.REPO_DIR + rel)}</a>")


def render_table(df, label, caption, rel, hl=None):
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    rows = "".join(f'<tr{" class=hl" if i == hl else ""}>' + "".join(f"<td>{html.escape(rs.fmt(v))}</td>" for v in r)
                   + "</tr>" for i, r in enumerate(df.astype(object).values))
    chip = f"<div>{src_chip(rel)}</div>" if rel else ""
    return (f'<div class="table-container"><div class="table-caption"><strong>{label}.</strong> {html.escape(caption)}</div>'
            f'<table class="arden-table"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>{chip}</div>')


def render_figure(b):
    path, rel = rs.figure_path(b)
    img = f'<img src="{b64(path)}" alt="{html.escape(b["caption"])}" loading="lazy">'
    cap = f'<div class="figure-caption"><strong>{b["label"]}.</strong> {inline(b["caption"])}<br>{src_chip(rel)}</div>'
    if b["type"] == "shot":
        return (f'<details class="code-shot"><summary><span class="ico">&lt;/&gt;</span>{b["label"]} · Code: '
                f'{inline(b["caption"])}<span class="chev">&#9656;</span></summary><div class="inner">{img}{cap}</div></details>')
    return f'<div class="figure-box">{img}{cap}</div>'


def explorer():
    prof = pd.read_csv(rs.TABLES / "table13_cluster_profiles.csv", index_col=0)
    js = []
    for c in (2, 0, 1, 3):
        r = prof.loc[c]
        name, role = rs.SEGMENTS[c]
        js.append(f"""{c}: {{name: "Cluster {c}: {name}", listings: "{int(r.listings)} listings ({r.share_of_listings_pct}%)",
            share: "{r.share_of_units_sold_pct}%", medPrice: "${r.median_price_usd:.2f}", medSold: "{r.median_units_sold:g} units",
            meanSold: "{r.mean_units_sold:,.0f} units", medStock: "{r.median_stock_level:g}", lastOne: "{r.pct_last_one}%",
            us: "{r.pct_ships_from_us}%", cat: "{r.top_product_type}", brands: "{r.top_brands}", role: "{role}"}}""")
    tabs = "".join(f'<button class="tab-btn" data-c="{c}" onclick="switchTab({c})">Cluster {c} · {rs.SEGMENTS[c][0]}</button>'
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
        f'<div class="rec-body"><p><span class="lbl">Evidence:</span> {inline(f)}</p><p><span class="lbl">Action:</span> {inline(a)}</p></div></div>'
        for cls, tag, title, f, a in rs.RECS)
    return f'<div class="rec-grid">{cards}</div>'


def kpis():
    return '<section class="kpi-strip">' + "".join(
        f'<div class="kpi-card{" accent" if acc else ""}"><div class="kpi-title">{t}</div><div class="kpi-val">{v}</div>'
        f'<div class="kpi-desc">{d}</div></div>' for t, v, d, acc in rs.KPIS) + "</section>"


def appendix(prefix):
    groups, out = {}, []
    for head, n, path, rel in rs.appendix_cells():
        groups.setdefault(head, []).append((n, rel))
    for head, cells in groups.items():
        out.append(f'<div class="code-group-label">{html.escape(head)}</div>')
        for n, rel in cells:
            out.append(f'<details class="code-shot"><summary><span class="ico">cell {n:02d}</span>Notebook code cell {n}'
                       f'<span class="chev">&#9656;</span></summary><div class="inner">'
                       f'<img src="{prefix}{rel}" alt="Notebook code cell {n}" loading="lazy">'
                       f'<div class="figure-caption">{src_chip(rel)}</div></div></details>')
    return '<div class="appendix-grid">' + "".join(out) + "</div>"


def build(prefix):
    blocks, labels, tables, wc = rs.load()
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
            parts.append(f'<section id="{b["id"]}" class="content-card"><div class="section-header"><h2>{inline(b["text"])}</h2>'
                         + (f'<span class="word-badge">{badge}</span>' if badge else "") + "</div>")
            open_card = True
        elif t == "part":
            close()
            words = wc["task1_total"] if "1" in b["tag"] else wc["task2"]
            parts.append(f'<div class="part-banner"><span class="tag">{b["tag"]}</span><span class="ttl">{b["title"]}</span>'
                         f'<span class="rule"></span><span class="word-badge">{words:,} words</span></div>')
        elif t in ("h2", "h3"):
            parts.append(f"<h3>{inline(b['text'])}</h3>")
        elif t == "para":
            parts.append(f"<p>{inline(b['text'])}</p>")
        elif t == "bullets" and section == "References":
            parts.append('<ul class="ref-list">' + "".join(f"<li>{inline(x)}</li>" for x in b["items"]) + "</ul>")
        elif t == "bullets":
            parts.append('<ul class="styled">' + "".join(f"<li>{inline(x)}</li>" for x in b["items"]) + "</ul>")
        elif t in ("figure", "shot"):
            parts.append(render_figure(b))
        elif t == "table":
            df, cap, rel = tables[b["key"]]
            parts.append(render_table(df, b["label"], cap, rel, rs.HIGHLIGHT.get(b["key"])))
        elif t == "callout":
            parts.append(f'<div class="callout-box"><strong>{inline(b["title"])}:</strong> {inline(b["text"])}</div>')
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
  <h1 class="hero-title">{rs.TITLE}</h1>
  <p class="hero-subtitle">An end-to-end unsupervised machine learning investigation comparing K-Means, Ward hierarchical clustering
  and DBSCAN across 1,000 marketplace listings, translated into evidence-based actions for inventory protection and catalogue strategy.</p>
  <div class="hero-meta-grid">
    <div class="meta-item"><span class="meta-label">Student ID</span><span class="meta-value">{rs.STUDENT_ID}</span></div>
    <div class="meta-item"><span class="meta-label">Module</span><span class="meta-value">COM7022 Machine Learning</span></div>
    <div class="meta-item"><span class="meta-label">Task 1 · Practical project</span><span class="meta-value">{wc['task1_total']:,} words</span></div>
    <div class="meta-item"><span class="meta-label">Task 2 · Critical report</span><span class="meta-value">{wc['task2']:,} words</span></div>
    <div class="meta-item"><span class="meta-label">Production model</span><span class="meta-value">K-Means (k = 4)</span></div>
  </div>
  <div class="hero-links">
    <a class="primary" href="{rs.REPO}" target="_blank" rel="noopener">GitHub repository ↗</a>
    <a href="{rs.repo_url('COM7022_Clustering_25199053.ipynb')}" target="_blank" rel="noopener">Notebook ↗</a>
    <a href="{rs.repo_url('COM7022_Portfolio_25199053_final.pdf')}" target="_blank" rel="noopener">Report (PDF) ↗</a>
  </div>
</section>"""
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COM7022 Portfolio · Product Clustering · {rs.STUDENT_ID}</title>
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
  <div class="nav-brand"><span>Arden University Berlin</span><span class="nav-badge">COM7022 Portfolio · {rs.STUDENT_ID}</span></div>
  <nav class="nav-links">{nav}<a href="{rs.REPO}" target="_blank" rel="noopener" style="color:var(--tiffany);font-weight:700">GitHub ↗</a></nav>
</header>
<main class="layout-container">
{hero}
{kpis()}
{''.join(parts)}
<div class="site-footer">COM7022 Machine Learning · Student ID {rs.STUDENT_ID} · All figures, tables and code are reproducible from
<a href="{rs.REPO}" target="_blank" rel="noopener">{rs.REPO}</a></div>
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


def main():
    for path, prefix in ((REVIEW_HTML, ""), (INDEX_HTML, "COM7022%20-%20Assignment/")):
        page, wc = build(prefix)
        path.write_text(page, encoding="utf-8")
        print(f"wrote {path.name}: {len(page) / 1e6:.1f} MB")
    print("word count:", wc)


if __name__ == "__main__":
    main()
