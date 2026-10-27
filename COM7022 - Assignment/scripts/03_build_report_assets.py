#!/usr/bin/env python3
"""Build the report-only visuals: code screenshots (rendered from notebook cells) and flowcharts.

Run:  python "COM7022 - Assignment/scripts/03_build_report_assets.py"
Outputs:
  output/screenshots/code01_*.png ...  syntax-highlighted images of the exact notebook cells
  output/figures/fig15_workflow.png, fig16_data_prep_flow.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import PythonLexer
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "COM7022_Clustering_25199053.ipynb"
SHOTS = ROOT / "output" / "screenshots"
FIGS = ROOT / "output" / "figures"
SHOTS.mkdir(parents=True, exist_ok=True)
MIDNIGHT, TIFFANY, GREY = "#002B49", "#0ABAB5", "#F2F5F7"

# notebook cell index -> (file stem, caption)
CELLS = {
    5:  ("code01_import_data", "Data import"),
    9:  ("code02_missing_values", "Missing-value audit"),
    17: ("code03_price_recovery", "Cleaning: recover price"),
    18: ("code04_sold_recovery", "Cleaning: recover units sold"),
    19: ("code05_stock_level", "Cleaning: stock level and censoring"),
    20: ("code06_product_type", "Cleaning: normalise product type"),
    21: ("code07_log_transform", "Transformation: log(1 + x)"),
    28: ("code08_scaling", "Scaling: StandardScaler"),
    30: ("code09_pca", "PCA"),
    33: ("code10_kmeans_scan", "K-Means: scan k"),
    40: ("code11_hierarchical", "Hierarchical: four linkages"),
    46: ("code12_dbscan_kdist", "DBSCAN: k-distance"),
    53: ("code13_metrics", "Evaluation metrics function"),
    54: ("code14_stability", "Stability (ARI) across seeds"),
}


def render_code(src: str, header: str, out: Path):
    fmt = ImageFormatter(font_name="DejaVu Sans Mono", font_size=15, line_numbers=True,
                         style="friendly", line_number_bg="#EEF2F5", line_number_fg="#6B7C8A",
                         image_pad=14, line_pad=3)
    code_png = out.with_suffix(".tmp.png")
    code_png.write_bytes(highlight(src.rstrip() + "\n", PythonLexer(), fmt))
    body = Image.open(code_png).convert("RGB")
    bar_h = 38
    img = Image.new("RGB", (body.width, body.height + bar_h), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, body.width, bar_h], fill=MIDNIGHT)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
    d.text((14, 10), header, fill="white", font=font)
    img.paste(body, (0, bar_h))
    img.save(out)
    code_png.unlink()


def box(ax, x, y, w, h, text, fc, tc="white", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec="none"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs,
            fontweight="bold", linespacing=1.25)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=MIDNIGHT, lw=1.6))


def workflow():
    fig, ax = plt.subplots(figsize=(12, 5.6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5.6); ax.axis("off")
    # row 1
    row1 = [("1. Business\nproblem", MIDNIGHT), ("2. Data import\n& audit", MIDNIGHT),
            ("3. Cleaning &\npre-processing", MIDNIGHT), ("4. Transform\n& scale", MIDNIGHT),
            ("5. Feature\nselection", MIDNIGHT)]
    for i, (t, c) in enumerate(row1):
        box(ax, 0.2 + i * 2.35, 4.2, 1.9, 1.0, t, c)
        if i: arrow(ax, 0.2 + i * 2.35 - 0.45, 4.7, 0.2 + i * 2.35, 4.7)
    arrow(ax, 11.0, 4.2, 11.0, 3.65)
    # row 2 (right to left)
    box(ax, 9.9, 2.65, 1.9, 0.95, "6. PCA\n(2-D view)", TIFFANY, MIDNIGHT)
    algos = [("K-Means\n(k = 4)", 7.55), ("Hierarchical\n(Ward)", 5.2), ("DBSCAN\n(eps 0.45)", 2.85)]
    for t, x in algos:
        box(ax, x, 2.65, 1.9, 0.95, t, TIFFANY, MIDNIGHT)
    arrow(ax, 9.9, 3.12, 9.45, 3.12)
    arrow(ax, 7.55, 3.12, 7.1, 3.12); arrow(ax, 5.2, 3.12, 4.75, 3.12)
    ax.text(5.8, 3.85, "7. Apply three clustering techniques", ha="center", fontsize=9.5,
            color=MIDNIGHT, style="italic")
    arrow(ax, 3.8, 2.65, 3.8, 2.05)
    # row 3
    row3 = [("8. Evaluate:\nsilhouette, DBI, CH,\nstability (ARI)", 1.2), ("9. Choose model\n(technical +\ne-commerce fit)", 4.0),
            ("10. Profile\nsegments", 6.8), ("11. Business\nactions", 9.4)]
    for i, (t, x) in enumerate(row3):
        box(ax, x, 0.75, 2.15, 1.2, t, MIDNIGHT if i < 3 else "#B03A2E", fs=8.6)
    arrow(ax, 3.35, 1.35, 4.0, 1.35); arrow(ax, 6.15, 1.35, 6.8, 1.35); arrow(ax, 8.95, 1.35, 9.4, 1.35)
    arrow(ax, 3.8, 2.05, 3.8, 1.95)
    ax.text(6, 0.25, "Student ID 25199053 - COM7022 approach: every step is recorded in the notebook and in the decision log",
            ha="center", fontsize=8.5, color="#555")
    fig.savefig(FIGS / "fig15_workflow.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def prep_flow():
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 4.6); ax.axis("off")
    steps = [("Raw file\n1,000 rows\n10 columns", MIDNIGHT),
             ("Quality audit\nmissing, duplicates,\nskew, dirty labels", MIDNIGHT),
             ("Recover\nprice, sold, stock\nfrom listing text", TIFFANY),
             ("Normalise\n~50 category labels\n-> 6 product types", TIFFANY),
             ("Remove\nunusable rows\n-> 997 kept", TIFFANY),
             ("log(1 + x)\nthen z-score\nscaling", MIDNIGHT)]
    for i, (t, c) in enumerate(steps):
        x = 0.15 + i * 1.95
        box(ax, x, 2.2, 1.7, 1.5, t, c, MIDNIGHT if c == TIFFANY else "white", fs=8.6)
        if i: arrow(ax, x - 0.25, 2.95, x, 2.95)
    notes = ["Evidence:\nTables 1-2,\nFig 1-2", "Evidence:\nCleaning log\n(Table 3)", "Rule: use data from\nthe same listing,\nno blind imputation",
             "Rule: typos and\ncase variants\nmerged", "Rule: keep rows\nwith price and\nsales", "Skew: 11.23 -> 0.25\n(sold)"]
    for i, t in enumerate(notes):
        ax.text(0.15 + i * 1.95 + 0.85, 1.7, t, ha="center", va="top", fontsize=8, color="#444", linespacing=1.3)
    fig.savefig(FIGS / "fig16_data_prep_flow.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    nb = json.loads(NB.read_text())
    for idx, (stem, cap) in CELLS.items():
        cell = nb["cells"][idx]
        assert cell["cell_type"] == "code", idx
        render_code("".join(cell["source"]), f"COM7022_Clustering_25199053.ipynb  |  {cap}", SHOTS / f"{stem}.png")
    workflow()
    prep_flow()
    # Appendix A: every code cell of the notebook, in order, as a screenshot
    app = SHOTS / "appendix"
    app.mkdir(exist_ok=True)
    n = 0
    for idx, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        n += 1
        render_code("".join(cell["source"]), f"COM7022_Clustering_25199053.ipynb  |  code cell {n} (notebook cell {idx})",
                    app / f"cell{n:02d}.png")
    print("built", len(CELLS), "code screenshots,", n, "appendix screenshots + 2 flowcharts")


if __name__ == "__main__":
    main()
