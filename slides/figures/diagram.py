import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

INK, SLATE, SNOW, FROST = "#2e3440", "#4c566a", "#e5e9f0", "#eceff4"
RED, CYAN, YELLOW, ORANGE = "#BE616A", "#8FBBBA", "#EBCB8B", "#CF8770"
W, H = 1600, 790
ROWS = [120, 245, 370, 495]
CARD = dict(x=625, y=172, w=350, h=270)
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
    rows = [["0.12", "-0.31", "0.08", "0.44"], ["-0.27", "0.05", "0.39", "-0.10"],
            ["0.33", "0.18", "-0.42", "0.07"], ["-0.06", "0.29", "0.11", "-0.35"]]
    cells = ""
    for r, row in enumerate(rows):
        yy = y + 78 + r * 46
        cells += f"<rect x='{x + 22}' y='{yy - 28}' width='{w - 44}' height='38' rx='6' fill='{FROST if r % 2 else SNOW}'/>"
        for c, value in enumerate(row):
            cells += text(x + 62 + c * 70, yy, value, 21, 400, INK, "middle")
        cells += text(x + w - 36, yy, "...", 21, 700, SLATE, "middle")
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='18' fill='white' stroke='{INK}' stroke-width='5'/>"
            + text(x + w / 2, y + 38, "Vectors", 30, 700, INK, "middle") + cells
            + text(x + w / 2, y + h - 22, "lists of numbers", 23, 400, SLATE, "middle"))


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


def diagram(stage):
    cy = CARD["y"] + CARD["h"] / 2
    left_x, right_x = CARD["x"], CARD["x"] + CARD["w"]
    icons = [protein, page, picture, sound]
    names = [("Proteins", "chains of amino acids"), ("Language", "words"), ("Images", "grids of pixels"), ("Audio", "sound waves")]
    parts = [step(180, 40, "1", "Embedding")]
    for icon, (title, sub), y in zip(icons, names, ROWS):
        parts += [icon(90, y), label(180, y, title, sub), flow(470, y, left_x - 34, cy)]
    parts += [head(left_x - 36, cy), vectors()]

    if stage >= 2:
        parts.append(step(1050, 40, "2", "Generation"))
        new = [("New proteins", "drug design"), ("New text", "chatbots"), ("New images", "image generators"), ("New audio", "voices, music")]
        for icon, (title, sub), y in zip(icons, new, ROWS):
            parts += [flow(right_x + 10, cy, 1180, y), head(1178, y), icon(1290, y, new=True), sparkle(1352, y - 46),
                      label(1380, y, title, sub)]

    if stage >= 3:
        y = 700
        parts += [f"<line x1='800' y1='{CARD['y'] + CARD['h'] + 8}' x2='800' y2='{y - 98}' stroke='{SLATE}' stroke-width='7' stroke-linecap='round'/>",
                  head(800, y - 100, "down"),
                  f"<rect x='250' y='{y - 66}' width='1100' height='132' rx='18' fill='{FROST}'/>",
                  f"<rect x='262' y='{y - 56}' width='376' height='112' rx='12' fill='#f6e7c8' stroke='{YELLOW}' stroke-width='4'/>",
                  bins(340, y), label(420, y, "Classification", "which group?"),
                  magnifier(720, y), label(800, y, "Search", "find similar"),
                  clusters(1060, y), label(1140, y, "Clustering", "sort a pile")]
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}'>{''.join(parts)}</svg>"


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for stage in (1, 2, 3):
        svg = OUT / f"diagram_{stage}.svg"
        svg.write_text(diagram(stage))
        subprocess.run(["rsvg-convert", "-w", "3200", str(svg), "-o", str(svg.with_suffix(".png"))], check=True)
