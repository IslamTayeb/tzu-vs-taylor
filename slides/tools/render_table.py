"""Render a presentation table from a JSON spec in the lab's slide style."""
import glob
import json
import os
import sys

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

for font_path in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "*.ttf")):
    font_manager.fontManager.addfont(font_path)
plt.rcParams.update({"font.family": os.environ.get("TABLE_FONT", "Carlito"), "svg.fonttype": "path"})

INK = "#2e3440"
RULE = "#2e3440"
STRIPE = "#eceff4"
TOTAL = "#d8dee9"
TINTS = {"yellow": ("#EBCB8B", 0.45), "cyan": ("#8FBBBA", 0.40), "red": ("#BE616A", 0.30), "orange": ("#CF8770", 0.35),
         "blue": ("#5E81AC", 0.28), "grey": ("#D8DEE9", 0.55)}
STRIPE_SHADE = 0.93
FONT = 13
EM = FONT / 72
CHAR = 0.52
PAD = 1.8
ROW = 2.1


def tint(name):
    """Opaque light tint of a palette color, so stripes underneath never show through."""
    color, alpha = TINTS[name]
    rgb = mcolors.to_rgb(color)
    return tuple(alpha * c + (1 - alpha) for c in rgb)


def width(text):
    """Approximate rendered width of text in em."""
    return CHAR * len(str(text))


def columns(spec):
    """Left edge of the label column, center of each data column and the right edge, in em."""
    rows = [row for section in spec["sections"] for row in section["rows"] + ([section["total"]] if section.get("total") else [])]
    swatch = 1.6 if any(row.get("swatch") for row in rows) else 0
    label = max([width(row["label"]) for row in rows] + [width(s["title"]) * 1.25 for s in spec["sections"]]) + swatch + PAD
    starts = {g["columns"][0] for g in spec.get("groups", [])}
    centers, spans, x = [], [], label
    for i, header in enumerate(spec["columns"]):
        if i in starts and i:
            x += 1.2
        w = max([width(header)] + [width(row["values"][i]) for row in rows]) + PAD
        w = max(w, 3.6)
        centers.append(x + w / 2)
        spans.append((x, x + w))
        x += w
    return centers, spans, x, swatch


def striped(color, row_index):
    """Darker shade of a cell color on alternate rows, so every row stays distinguishable inside highlights."""
    if row_index % 2:
        return color
    rgb = mcolors.to_rgb(color)
    return tuple(STRIPE_SHADE * c for c in rgb)


def highlights(spec):
    """Background color for each (row label, column) cell, row and column named in the spec."""
    cells, rows, cols = {}, {}, {}
    for item in spec.get("highlight", []):
        color = tint(item.get("color", "yellow"))
        if "cell" in item:
            cells[tuple(item["cell"])] = color
        elif "row" in item:
            rows[item["row"]] = color
        elif "column" in item:
            cols[item["column"]] = color
    return cells, rows, cols


def draw_section(ax, spec, section, centers, spans, right, swatch, y):
    """Draw one titled block of the table from height y downward and return the height below it."""
    ax.text(0, y, section["title"], fontsize=FONT + 3, fontweight="bold", color=INK, va="center")
    for group in spec.get("groups", []):
        a, b = group["columns"][0], group["columns"][-1]
        ax.text((centers[a] + centers[b]) / 2, y, group["label"], fontsize=FONT, color=INK, ha="center", va="center")
        ax.plot([centers[a] - 1.6, centers[b] + 1.6], [y - 1.0, y - 1.0], color=RULE, lw=1)
    for i, header in enumerate(spec["columns"]):
        ax.text(centers[i], y - 2.1, header, fontsize=FONT, color=INK, ha="center", va="center")
    ax.plot([0, right], [y - 3.1, y - 3.1], color=RULE, lw=1.4)
    y -= 3.1 + ROW / 2
    cells, row_colors, col_colors = highlights(spec)
    rows = section["rows"] + ([section["total"]] if section.get("total") else [])
    for r, row in enumerate(rows):
        total = section.get("total") is row
        base = TOTAL if total else (STRIPE if r % 2 == 0 else "white")
        base = row_colors.get(row["label"], base)
        ax.add_patch(Rectangle((0, y - ROW / 2), right, ROW, color=base, zorder=0, lw=0))
        for i in range(len(centers)):
            color = cells.get((row["label"], i)) or col_colors.get(i)
            if color and not (row["label"] in row_colors and (row["label"], i) not in cells):
                ax.add_patch(Rectangle((spans[i][0], y - ROW / 2), spans[i][1] - spans[i][0], ROW, color=striped(color, r), zorder=1, lw=0))
        if total:
            ax.plot([0, right], [y + ROW / 2, y + ROW / 2], color=RULE, lw=1)
        x = 0.6
        if row.get("swatch"):
            ax.add_patch(Rectangle((x, y - 0.55), 1.0, 1.1, facecolor=row["swatch"], edgecolor=INK, lw=0.8, zorder=2))
            x += swatch
        ax.text(x, y, row["label"], fontsize=FONT, color=INK, va="center", zorder=3)
        for i, value in enumerate(row["values"]):
            ax.text(centers[i], y, str(value), fontsize=FONT, color=INK, ha="center", va="center", zorder=3)
        y -= ROW
    ax.plot([0, right], [y + ROW / 2, y + ROW / 2], color=RULE, lw=1.4)
    return y - ROW


def render(spec, out):
    """Draw every section and the footnote, then save at 600 DPI."""
    centers, spans, right, swatch = columns(spec)
    notes = spec.get("footnote", [])
    height = sum(3.1 + ROW * (len(s["rows"]) + bool(s.get("total")) + 1) for s in spec["sections"]) + 1.3 * len(notes) + 1
    fig = plt.figure(figsize=(right * EM, height * EM))
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.axis("off")
    ax.set_xlim(0, right)
    ax.set_ylim(-height + 1, 1)
    y = 0.0
    for section in spec["sections"]:
        y = draw_section(ax, spec, section, centers, spans, right, swatch, y)
    y += ROW / 2
    for line in notes:
        ax.text(0, y, line, fontsize=FONT - 2, color=INK, va="center")
        y -= 1.3
    fig.savefig(out, dpi=600, bbox_inches="tight", pad_inches=0.15, facecolor="white")
    fig.savefig(out.rsplit(".", 1)[0] + ".svg", bbox_inches="tight", pad_inches=0.15, facecolor="white")


if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
