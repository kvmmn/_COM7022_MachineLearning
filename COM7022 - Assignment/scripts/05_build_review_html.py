#!/usr/bin/env python3
"""Build the self-contained GitHub Pages review page from the final report (.docx).

pandoc converts the report, so the page always shows exactly the numbers in the Word/PDF file.
A small interactive segment explorer (from output/tables/table13_cluster_profiles.csv) is added on top.
Writes COM7022_Draft_Review_25199053.html and ../index.html.   Run after 04_build_report_docx.py.
"""
import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "COM7022_Portfolio_25199053_final.docx"
PROFILE = ROOT / "output" / "tables" / "table13_cluster_profiles.csv"
OUTS = [ROOT / "COM7022_Draft_Review_25199053.html", ROOT.parent / "index.html"]

CSS = """
:root{--mid:#002B49;--tif:#0ABAB5;--bg:#F2F5F7;--ink:#1c2b36}
body{max-width:none!important;padding:0!important;font-family:Calibri,'Segoe UI',Arial,sans-serif;color:var(--ink);background:var(--bg);margin:0;line-height:1.55}
body>*{max-width:900px;margin-left:auto;margin-right:auto;padding-left:16px;padding-right:16px}
header.top{max-width:none;background:var(--mid);color:#fff;padding:18px 24px;margin:0 0 24px}
header.top b{color:var(--tif)}
h1,h2,h3{color:var(--mid)} h1{border-bottom:3px solid var(--tif);padding-bottom:4px}
img{max-width:100%;height:auto;display:block;margin:10px auto}
table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0;background:#fff}
th{background:var(--mid);color:#fff;text-align:left} td,th{border:1px solid #cfd8de;padding:4px 7px;vertical-align:top}
tr:nth-child(even) td{background:#f6f9fa}
p>em{font-size:12.5px;color:#4a5b66}
a{color:#008f8b;word-break:break-all}
.explorer{background:#fff;border:1px solid #cfd8de;border-radius:10px;padding:16px;margin:20px auto}
.tabs button{border:1px solid var(--mid);background:#fff;color:var(--mid);padding:6px 10px;margin:0 6px 6px 0;border-radius:6px;cursor:pointer}
.tabs button.on{background:var(--mid);color:#fff}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-top:8px}
.kpi{background:var(--bg);border-radius:8px;padding:8px}.kpi b{display:block;font-size:20px;color:var(--mid)}
"""

NAMES = {0: "Premium designer", 1: "Budget", 2: "Best-sellers", 3: "Low-stock tail"}


def explorer():
    prof = pd.read_csv(PROFILE, index_col=0)
    data = {}
    for c in prof.index:
        r = prof.loc[c]
        data[int(c)] = {"name": NAMES[int(c)], "Listings": f"{int(float(r['listings']))} ({r['share_of_listings_pct']}%)",
                        "Median price": f"${float(r['median_price_usd']):.2f}", "Median units sold": f"{float(r['median_units_sold']):g}",
                        "Share of all units sold": f"{r['share_of_units_sold_pct']}%", "Median stock": f"{float(r['median_stock_level']):g}",
                        "Marked 'Last One'": f"{r['pct_last_one']}%", "Top product type": r["top_product_type"],
                        "Top brands": r["top_brands"]}
    tabs = "".join(f'<button id="b{k}" onclick="show({k})">Cluster {k}: {v["name"]}</button>' for k, v in data.items())
    return f"""<section class="explorer"><h2>Interactive segment explorer</h2><div class="tabs">{tabs}</div><div id="kp" class="kpis"></div>
<script>const D={json.dumps(data)};function show(k){{document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));
document.getElementById('b'+k).classList.add('on');const d=D[k];let h='';for(const[x,y]of Object.entries(d)){{if(x!=='name')h+='<div class="kpi">'+x+'<b>'+y+'</b></div>'}}
document.getElementById('kp').innerHTML=h}};show(2);</script></section>"""


def main():
    with tempfile.TemporaryDirectory() as td:
        body = Path(td) / "body.html"
        subprocess.run(["pandoc", str(DOCX), "-f", "docx", "-t", "html5", "--embed-resources", "--standalone",
                        "--metadata", "title=COM7022 Portfolio 25199053", "-o", str(body), "--extract-media", td],
                       check=True, cwd=ROOT)
        html = body.read_text()
    html = html.replace("</style>", CSS + "</style>", 1) if "</style>" in html else html.replace("</head>", f"<style>{CSS}</style></head>")
    banner = ('<header class="top"><b>COM7022 Machine Learning</b> | Student ID 25199053 | Review copy of the final report. '
              'Repository: <a style="color:#fff" href="https://github.com/kvmmn/_COM7022_MachineLearning">kvmmn/_COM7022_MachineLearning</a></header>')
    html = html.replace("<body>", "<body>" + banner + explorer(), 1)
    for o in OUTS:
        o.write_text(html)
        print("wrote", o, round(o.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
