import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

INK, SLATE, SNOW, FROST = "#2e3440", "#4c566a", "#e5e9f0", "#eceff4"
RED, CYAN, YELLOW, ORANGE = "#BE616A", "#8FBBBA", "#EBCB8B", "#CF8770"
W, H = 1600, 790
ROWS = [210, 335, 460, 585]
CARD = dict(x=545, y=247, w=420, h=300)
FONT = "font-family='Lato, Carlito, Calibri, sans-serif'"


def text(x, y, s, size=30, weight=700, fill=INK, anchor="start"):
    return f"<text x='{x}' y='{y}' {FONT} font-size='{size}' font-weight='{weight}' fill='{fill}' text-anchor='{anchor}'>{s}</text>"


def label(x, y, title, sub):
    return text(x, y - 6, title) + text(x, y + 28, sub, 23, 400, SLATE)


def protein(cx, cy, new=False):
    colors = [CYAN, RED, YELLOW, ORANGE] if not new else [ORANGE, YELLOW, CYAN, RED]
    pts = [(cx - 52 + 13 * i, cy + 30 * math.sin(i * 0.95 + (1.4 if new else 0))) for i in range(9)]
    path = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    beads = "".join(f"<circle cx='{x:.0f}' cy='{y:.0f}' r='12' fill='{colors[i % 4]}' stroke='{INK}' stroke-width='3'/>"
                    for i, (x, y) in enumerate(pts))
    return f"<path d='{path}' fill='none' stroke='{INK}' stroke-width='5'/>{beads}"


def page(cx, cy, new=False):
    x, y = cx - 42, cy - 54
    lines = "".join(f"<rect x='{x + 14}' y='{y + 26 + 18 * i}' width='{[56, 44, 56, 30][i]}' height='7' rx='3.5' fill='{RED if new and i == 1 else SLATE}'/>"
                    for i in range(4))
    return (f"<path d='M{x},{y} h60 l24,24 v84 h-84 z' fill='white' stroke='{INK}' stroke-width='4' stroke-linejoin='round'/>"
            f"<path d='M{x + 60},{y} v24 h24' fill='{SNOW}' stroke='{INK}' stroke-width='4' stroke-linejoin='round'/>{lines}")


def picture(cx, cy, new=False):
    x, y = cx - 56, cy - 44
    sky, hill = (FROST, CYAN) if not new else ("#f6e7c8", ORANGE)
    return (f"<rect x='{x}' y='{y}' width='112' height='88' rx='8' fill='{sky}' stroke='{INK}' stroke-width='4'/>"
            f"<circle cx='{x + 84}' cy='{y + 26}' r='12' fill='{YELLOW}' stroke='{INK}' stroke-width='3'/>"
            f"<path d='M{x + 6},{y + 82} l34,-44 l26,30 l14,-16 l26,30 z' fill='{hill}' stroke='{INK}' stroke-width='3' stroke-linejoin='round'/>")


def sound(cx, cy, new=False):
    heights = [14, 30, 52, 76, 44, 88, 60, 34, 70, 46, 22, 12]
    if new:
        heights = heights[::-1]
    bars = "".join(f"<rect x='{cx - 64 + 11 * i}' y='{cy - h / 2}' width='7' height='{h}' rx='3.5' fill='{RED if i in (3, 5, 8) else INK}'/>"
                   for i, h in enumerate(heights))
    return bars


def sparkle(cx, cy):
    return (f"<path d='M{cx},{cy - 16} L{cx + 4},{cy - 4} L{cx + 16},{cy} L{cx + 4},{cy + 4} L{cx},{cy + 16} L{cx - 4},{cy + 4} L{cx - 16},{cy} L{cx - 4},{cy - 4} z' "
            f"fill='{YELLOW}' stroke='{INK}' stroke-width='2.5' stroke-linejoin='round'/>")


def vectors():
    x, y, w, h = CARD["x"], CARD["y"], CARD["w"], CARD["h"]
    columns = [["0.12", "-0.31", "0.08"], ["-0.27", "0.05", "0.39"], ["0.33", "0.18", "-0.42"], ["-0.06", "0.29", "0.11"]]
    col_w, gap = 76, 22
    left = x + (w - (4 * col_w + 3 * gap)) / 2
    top, bottom = y + 64, y + h - 62
    cells = ""
    for c, values in enumerate(columns):
        x0 = left + c * (col_w + gap)
        cx = x0 + col_w / 2
        bracket = f"stroke='{INK}' stroke-width='3.5' fill='none' stroke-linejoin='round'"
        cells += f"<path d='M{x0 + 9},{top} h-9 v{bottom - top} h9' {bracket}/>"
        cells += f"<path d='M{x0 + col_w - 9},{top} h9 v{bottom - top} h-9' {bracket}/>"
        for r, value in enumerate(values):
            cells += text(cx, top + 34 + r * 36, value, 21, 400, INK, "middle")
        cells += text(cx, top + 34 + 3 * 36 + 2, "&#8942;", 24, 700, SLATE, "middle")
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='18' fill='white' stroke='{INK}' stroke-width='5'/>"
            + text(x + w / 2, y + 40, "Vectors", 30, 700, INK, "middle") + cells
            + text(x + w / 2, y + h - 18, "lists of numbers", 23, 400, SLATE, "middle"))


def flow(x1, y1, x2, y2, color=SLATE):
    mid = (x1 + x2) / 2
    return f"<path d='M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2}' fill='none' stroke='{color}' stroke-width='7' stroke-linecap='round'/>"


def head(x, y, direction="right", color=SLATE):
    if direction == "right":
        return f"<path d='M{x},{y - 16} L{x + 26},{y} L{x},{y + 16} z' fill='{color}'/>"
    return f"<path d='M{x - 16},{y} L{x},{y + 26} L{x + 16},{y} z' fill='{color}'/>"


def step(x, y, n, name):
    return (f"<circle cx='{x}' cy='{y}' r='24' fill='{INK}'/>" + text(x, y + 10, n, 28, 700, "white", "middle")
            + text(x + 38, y + 11, name, 34))


def bins(cx, cy):
    out = ""
    for dx, tint, dot in [(-36, "#f1d6d9", RED), (36, "#d6e8e7", CYAN)]:
        out += f"<rect x='{cx + dx - 30}' y='{cy - 34}' width='60' height='68' rx='8' fill='{tint}' stroke='{INK}' stroke-width='4'/>"
        out += "".join(f"<circle cx='{cx + dx + ox}' cy='{cy + oy}' r='8' fill='{dot}' stroke='{INK}' stroke-width='2.5'/>"
                       for ox, oy in [(-10, -12), (10, -6), (-4, 12)])
    return out


def magnifier(cx, cy):
    lines = "".join(f"<rect x='{cx - 50}' y='{cy - 30 + 20 * i}' width='{[70, 52, 62][i]}' height='8' rx='4' fill='{SLATE}'/>" for i in range(3))
    return (lines + f"<circle cx='{cx + 22}' cy='{cy + 4}' r='24' fill='white' fill-opacity='.85' stroke='{INK}' stroke-width='5'/>"
            f"<line x1='{cx + 40}' y1='{cy + 22}' x2='{cx + 58}' y2='{cy + 40}' stroke='{INK}' stroke-width='8' stroke-linecap='round'/>")


def clusters(cx, cy):
    groups = [(-38, -14, RED), (30, -20, CYAN), (0, 26, YELLOW)]
    return "".join(f"<circle cx='{cx + gx + ox}' cy='{cy + gy + oy}' r='8' fill='{c}' stroke='{INK}' stroke-width='2.5'/>"
                   for gx, gy, c in groups for ox, oy in [(-10, -6), (10, -4), (0, 10), (-2, -18)])


def scaled(svg, cx, cy, s):
    return f"<g transform='translate({cx},{cy}) scale({s}) translate({-cx},{-cy})'>{svg}</g>"


def small_label(x, y, title, sub):
    return text(x, y - 4, title, 27) + text(x, y + 24, sub, 20, 400, SLATE)


GEN_ROWS = [105, 190, 275, 360]
USE_ROWS = [520, 605, 690]


def diagram(stage):
    cy = CARD["y"] + CARD["h"] / 2
    left_x, right_x = CARD["x"], CARD["x"] + CARD["w"]
    icons = [protein, page, picture, sound]
    names = [("Proteins", "chains of amino acids"), ("Language", "words"), ("Images", "grids of pixels"), ("Audio", "sound waves")]
    parts = [step(180, 40, "1", "Embedding")]
    for icon, (title, sub), y in zip(icons, names, ROWS):
        parts += [scaled(icon(90, y), 90, y, 0.8), label(170, y, title, sub), flow(470, y, left_x - 34, cy)]
    parts += [head(left_x - 36, cy), vectors()]

    icon_x, label_x, arrow_x = 1255, 1335, 1150
    if stage >= 2:
        parts.append(step(1180, 40, "2", "Generation"))
        new = [("New proteins", "drug design"), ("New text", "chatbots"), ("New images", "image generators"), ("New audio", "voices, music")]
        for icon, (title, sub), y in zip(icons, new, GEN_ROWS):
            parts += [flow(right_x + 10, cy, arrow_x, y), head(arrow_x - 2, y),
                      scaled(icon(icon_x, y, new=True) + sparkle(icon_x + 66, y - 40), icon_x, y, 0.6),
                      small_label(label_x, y, title, sub)]

    if stage >= 3:
        parts.append(text(1180, USE_ROWS[0] - 62, "...and more", 30, 700, INK))
        parts.append(f"<rect x='{icon_x - 62}' y='{USE_ROWS[0] - 40}' width='{1585 - icon_x + 62}' height='80' rx='12' "
                     f"fill='#f6e7c8' stroke='{YELLOW}' stroke-width='4'/>")
        uses = [(bins, "Classification", "which group?"), (magnifier, "Search", "find similar"), (clusters, "Clustering", "sort a pile")]
        for (icon, title, sub), y in zip(uses, USE_ROWS):
            parts += [flow(right_x + 10, cy, arrow_x, y), head(arrow_x - 2, y), scaled(icon(icon_x, y), icon_x, y, 0.66),
                      small_label(label_x, y, title, sub)]
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}'>{''.join(parts)}</svg>"


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for stage in (1, 2, 3):
        svg = OUT / f"diagram_{stage}.svg"
        source = OUT / f"diagram_{stage}_source.svg"
        source.write_text(diagram(stage))
        subprocess.run(["rsvg-convert", "-w", "3200", str(source), "-o", str(svg.with_suffix(".png"))], check=True)
        subprocess.run(["rsvg-convert", "-f", "svg", str(source), "-o", str(svg)], check=True)
        source.unlink()
