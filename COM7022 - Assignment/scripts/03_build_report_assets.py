#!/usr/bin/env python3
"""Build the report-only visuals at print resolution: code screenshots and diagrams.

Everything is drawn at its final printed size (the report text width is 6.6 in) at 300 dpi, in the same
type family and palette as the notebook figures, so the report can insert each image without rescaling.

Run:  python "COM7022 - Assignment/scripts/03_build_report_assets.py"
Outputs:
  output/screenshots/code01_*.png ...       key notebook cells shown in the report body
  output/screenshots/appendix/cellNN.png    every notebook code cell (Appendix A)
  output/figures/fig15_workflow.png, fig16_data_prep_flow.png, fig17_segment_actions.png
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import PythonLexer
from pygments.style import Style
from pygments.token import Comment, Keyword, Name, Number, Operator, String, Text

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "COM7022_Clustering_25199053.ipynb"
SHOTS = ROOT / "output" / "screenshots"
FIGS = ROOT / "output" / "figures"
TABLES = ROOT / "output" / "tables"
SHOTS.mkdir(parents=True, exist_ok=True)
(SHOTS / "appendix").mkdir(exist_ok=True)

MIDNIGHT, MIDNIGHT_SOFT, TIFFANY, TIFFANY_DEEP = "#002B49", "#1A4A6B", "#66C9BA", "#3AA89A"
MIST, PAPER, GRID, MUTE = "#E6F5F2", "#F7FAFB", "#D5DEE3", "#5A6B75"
SEGMENT = {0: "#2F6690", 1: "#C99A2E", 2: TIFFANY_DEEP, 3: "#C8553D"}     # same as the notebook
DPI, TEXT_WIDTH = 300, 6.6
FONT_REG = "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf"

plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Carlito", "Calibri", "Arial", "DejaVu Sans"],
                     "font.size": 8.5, "savefig.dpi": DPI, "figure.dpi": 100})

# notebook cell index -> (file stem, label shown in the header bar)
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
}


# ----------------------------------------------------------------------------- code screenshots
class ArdenCode(Style):
    """Print-friendly syntax colours in the report palette."""
    background_color = PAPER
    default_style = ""
    styles = {
        Text: MIDNIGHT, Comment: "italic " + MUTE, Keyword: "bold " + MIDNIGHT, Name: MIDNIGHT,
        Name.Function: "bold #2F6690", Name.Builtin: "#2F6690", String: "#1F8A7D", Number: "#C8553D",
        Operator: MIDNIGHT_SOFT,
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
    max_w = int(TEXT_WIDTH * DPI)
    width = max_w                                            # every screenshot spans the full text width
    if body.width > max_w:                                   # very long lines: shrink to the text width
        body = body.resize((max_w, int(body.height * max_w / body.width)), Image.LANCZOS)
    bar_h = 62
    img = Image.new("RGB", (width, body.height + bar_h), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, bar_h], fill=MIDNIGHT)
    d.rectangle([0, 0, 8, bar_h], fill=TIFFANY)
    f_reg, f_bold = ImageFont.truetype(FONT_REG, 28), ImageFont.truetype(FONT_BOLD, 29)
    name = "COM7022_Clustering_25199053.ipynb"
    d.text((26, 14), name, fill="#A9C4D4", font=f_reg)
    x = 26 + f_reg.getlength(name) + 18
    d.text((x, 14), "|", fill="#5F7F95", font=f_reg)
    d.text((x + 22, 13), header, fill="white", font=f_bold)
    gutter = Image.new("RGB", (width, body.height), PAPER)   # extend the code panel to the full width
    gutter.paste(body, (0, 0))
    img.paste(gutter, (0, bar_h))
    d.rectangle([0, 0, width - 1, img.height - 1], outline=GRID, width=2)
    img.save(out, dpi=(DPI, DPI))


# ----------------------------------------------------------------------------- diagram primitives
def canvas(height):
    fig = plt.figure(figsize=(TEXT_WIDTH, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, TEXT_WIDTH); ax.set_ylim(0, height); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc="white", ec=GRID, tc=MIDNIGHT, bold=False, size=7.5, accent=None, lw=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05", fc=fc, ec=ec, lw=lw))
    if accent:
        ax.add_patch(FancyBboxPatch((x, y), 0.05, h, boxstyle="square,pad=0", fc=accent, ec="none"))
    ax.text(x + w / 2 + (0.025 if accent else 0), y + h / 2, text, ha="center", va="center", color=tc,
            fontsize=size, fontweight="bold" if bold else "normal", linespacing=1.15)


def arrow(ax, x1, y1, x2, y2, color=MIDNIGHT_SOFT, lw=0.9):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=7, shrinkA=0, shrinkB=0))


def line(ax, xs, ys, color=MIDNIGHT_SOFT, lw=0.9):
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="butt")


def save(fig, name):
    fig.savefig(FIGS / name, dpi=DPI, facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------------- figures
def workflow(models):
    """Four phase columns on one grid; uniform boxes; straight connectors; models as parallel branches."""
    H = 3.55
    fig, ax = canvas(H)
    cols = ["1  Understand", "2  Prepare", "3  Model", "4  Evaluate and act"]
    gap, x0 = 0.22, 0.03
    cw = (TEXT_WIDTH - 2 * x0 - 3 * gap) / 4
    xs = [x0 + i * (cw + gap) for i in range(4)]
    top, head_h = H - 0.08, 0.30
    body_top, body_bot = top - head_h - 0.10, 0.12
    for x, title in zip(xs, cols):
        ax.add_patch(FancyBboxPatch((x, body_bot), cw, top - body_bot, boxstyle="round,pad=0,rounding_size=0.06",
                                    fc=PAPER, ec=GRID, lw=0.6))
        ax.add_patch(FancyBboxPatch((x, top - head_h), cw, head_h, boxstyle="round,pad=0,rounding_size=0.06",
                                    fc=MIDNIGHT, ec="none"))
        ax.text(x + cw / 2, top - head_h / 2, title, ha="center", va="center", color="white", fontsize=8,
                fontweight="bold")
    stacks = {
        0: ["Business problem\nmulti-seller catalogue", "Objectives\nO1–O5", "Data import\n1,000 listings × 10",
            "Quality audit\nmissing · skew · censoring"],
        1: ["Recover values from\nlisting text", "Normalise labels\n63 → 6 product types", "log(1 + x) and\nz-score scaling",
            "Select 3 features\nprice · sales · stock"],
        3: ["Internal indices\nsilhouette · DBI · CH", "Stability and\nsensitivity (ARI)", "Model choice\ntechnical + e-commerce",
            "Segment profiles\n→ business actions"],
    }
    bw, bh = cw - 0.16, 0.44

    def stack_positions(n):
        span = body_top - body_bot - 0.06
        step = span / n
        return [body_top - step * (i + 0.5) - bh / 2 for i in range(n)]

    centres = {}
    for c, items in stacks.items():
        ys = stack_positions(4)                      # identical row grid in columns 1, 2 and 4
        for i, (t, y) in enumerate(zip(items, ys)):
            last = (c == 3 and i == len(items) - 1)
            box(ax, xs[c] + 0.08, y, bw, bh, t, fc=MIDNIGHT if last else "white", ec=MIDNIGHT if last else GRID,
                tc="white" if last else MIDNIGHT, size=7.2, accent=None if last else TIFFANY_DEEP)
            if i:
                arrow(ax, xs[c] + cw / 2, ys[i - 1], xs[c] + cw / 2, y + bh)
        centres[c] = [y + bh / 2 for y in ys]
    # model column: PCA view on the first grid row, models as parallel branches spanning rows 2-4
    grid = stack_positions(4)
    box(ax, xs[2] + 0.08, grid[0], bw, bh, "PCA: 2-D view\n(78.7% variance)", size=7.2, accent=TIFFANY)
    n = len(models)
    top_m, bot_m = grid[1] + bh, grid[3]
    mh = min(bh * 0.78, (top_m - bot_m) / (n + (n - 1) * 0.35))
    pitch = (top_m - bot_m - mh) / (n - 1)
    model_ys = [top_m - mh / 2 - i * pitch for i in range(n)]
    bus_x = xs[2] + 0.17
    line(ax, [bus_x, bus_x], [grid[0], model_ys[-1]])
    for (name, highlight), yc in zip(models, model_ys):
        line(ax, [bus_x, xs[2] + 0.30], [yc, yc])
        box(ax, xs[2] + 0.30, yc - mh / 2, bw - 0.22, mh, name, fc=MIST if highlight else "white",
            ec=TIFFANY_DEEP if highlight else GRID, bold=highlight, size=7.2, lw=0.9 if highlight else 0.7)
    # phase-to-phase connectors at a common height, between column frames
    yc = (body_top + body_bot) / 2
    for i in range(3):
        arrow(ax, xs[i] + cw + 0.02, yc, xs[i + 1] - 0.02, yc, color=MIDNIGHT, lw=1.1)
    save(fig, "fig15_workflow.png")


def prep_flow():
    H = 1.95
    fig, ax = canvas(H)
    steps = [("Raw extract", "1,000 rows\n10 columns"), ("Quality audit", "missing · duplicates\nskew · labels"),
             ("Recover", "price, sales, stock\nfrom listing text"), ("Normalise", "63 labels →\n6 product types"),
             ("Retain", "3 unusable rows\nremoved → 997"), ("Transform", "log(1 + x)\nthen z-score")]
    notes = ["Tables 1–2", "Figures 2–3", "no blind imputation", "typos and case merged", "best-sellers kept",
             "skew 9.72 → 0.52"]
    n, gap = len(steps), 0.13
    w = (TEXT_WIDTH - 0.09 - gap * (n - 1)) / n
    y, h = 0.62, 1.12
    for i, ((title, sub), note) in enumerate(zip(steps, notes)):
        x = 0.045 + i * (w + gap)
        dark = i in (0, n - 1)
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05",
                                    fc=MIDNIGHT if dark else "white", ec=MIDNIGHT if dark else GRID, lw=0.7))
        ax.add_patch(FancyBboxPatch((x, y + h - 0.06), w, 0.06, boxstyle="square,pad=0",
                                    fc=TIFFANY if dark else TIFFANY_DEEP, ec="none"))
        ax.text(x + 0.09, y + h - 0.25, f"{i + 1:02d}", color=TIFFANY if dark else TIFFANY_DEEP, fontsize=7,
                fontweight="bold", va="center")
        ax.text(x + w / 2, y + h - 0.47, title, ha="center", va="center", fontsize=8.2, fontweight="bold",
                color="white" if dark else MIDNIGHT)
        ax.text(x + w / 2, y + 0.30, sub, ha="center", va="center", fontsize=7, linespacing=1.2,
                color="#D5DEE3" if dark else MUTE)
        ax.text(x + w / 2, 0.30, note, ha="center", va="center", fontsize=6.8, color=MIDNIGHT_SOFT, style="italic")
        line(ax, [x + w / 2, x + w / 2], [0.42, y], color=GRID, lw=0.6)
        if i:
            arrow(ax, x - gap + 0.015, y + h / 2, x - 0.015, y + h / 2, color=MIDNIGHT, lw=1.0)
    line(ax, [0.045, TEXT_WIDTH - 0.045], [0.12, 0.12], color=GRID, lw=0.6)
    save(fig, "fig16_data_prep_flow.png")


def segment_actions():
    """Executive view: share of listings vs share of units sold per segment, with the recommended action."""
    prof = pd.read_csv(TABLES / "table13_cluster_profiles.csv", index_col=0)
    order = [(2, "Best-sellers", "PROTECT"), (0, "Premium designer", "GROW"), (1, "Budget", "REPOSITION"),
             (3, "Low-stock tail", "AUDIT")]
    fig = plt.figure(figsize=(TEXT_WIDTH, 2.7))
    ax = fig.add_axes([0.17, 0.16, 0.66, 0.74])
    for i, (c, name, act) in enumerate(order):
        lst, units = prof.loc[c, "share_of_listings_pct"], prof.loc[c, "share_of_units_sold_pct"]
        col = SEGMENT[c]
        ax.barh(i - 0.17, units, height=0.32, color=col)
        ax.barh(i + 0.17, lst, height=0.32, color=col, alpha=0.3)
        if units > 60:
            ax.text(units - 1.5, i - 0.17, f"{units:.1f}% of units sold", va="center", ha="right", fontsize=7.5,
                    color="white", fontweight="bold")
        else:
            ax.text(units + 1.2, i - 0.17, f"{units:.1f}% of units sold", va="center", fontsize=7.5, color=MIDNIGHT,
                    fontweight="bold")
        ax.text(lst + 1.2, i + 0.17, f"{lst:.1f}% of listings", va="center", fontsize=7.2, color=MUTE)
        ax.text(106, i, act, ha="left", va="center", fontsize=7.5, fontweight="bold", color="white", clip_on=False,
                bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.15", fc=col, ec="none"))
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"Cluster {c}\n{n}" for c, n, _ in order], fontsize=7.8, color=MIDNIGHT)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of catalogue (%)", fontsize=8, color=MIDNIGHT)
    ax.tick_params(axis="x", labelsize=7.5, colors=MUTE, width=0.6, length=2.5)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#9AAAB4"); ax.spines["bottom"].set_linewidth(0.6)
    ax.text(106, -0.72, "ACTION", fontsize=7, color=MUTE, fontweight="bold", va="center", clip_on=False)
    fig.savefig(FIGS / "fig17_segment_actions.png", dpi=DPI, facecolor="white")
    plt.close(fig)


def main():
    nb = json.loads(NB.read_text())
    for idx, (stem, cap) in CELLS.items():
        cell = nb["cells"][idx]
        assert cell["cell_type"] == "code", (idx, "".join(cell["source"])[:60])
        render_code("".join(cell["source"]), cap, SHOTS / f"{stem}.png")
    n = 0
    for idx, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            n += 1
            render_code("".join(cell["source"]), f"code cell {n}", SHOTS / "appendix" / f"cell{n:02d}.png")
    for old in (SHOTS / "appendix").glob("cell*.png"):          # drop screenshots of cells that no longer exist
        if int(old.stem[4:]) > n:
            old.unlink()
    models = [("K-Means  (k = 4)", True), ("Ward hierarchical", False), ("DBSCAN", False), ("HDBSCAN", False)]
    if (TABLES / "table17_tabclustpfn.csv").exists():
        models.append(("TabClustPFN", False))
    workflow(models)
    prep_flow()
    segment_actions()
    print("built", len(CELLS), "body screenshots,", n, "appendix screenshots, 3 diagrams")


if __name__ == "__main__":
    main()
