import math
import subprocess

from diagram import FROST, INK, OUT, SLATE, flow, head, text

SPAM, REAL = "#CF8770", "#4c566a"


def n(k):
    return f"<tspan font-style='italic'>n</tspan><tspan baseline-shift='sub' font-size='70%'>{k}</tspan>"


def envelope(cx, cy, tag=None, color=SLATE):
    x, y = cx - 52, cy - 36
    out = (f"<rect x='{x}' y='{y}' width='104' height='72' rx='8' fill='white' stroke='{INK}' stroke-width='4'/>"
           f"<path d='M{x + 4},{y + 6} L{cx},{cy + 6} L{x + 100},{y + 6}' fill='none' stroke='{INK}' stroke-width='4' stroke-linejoin='round'/>")
    if tag:
        out += pill(cx + 72, cy, tag, color, small=True, anchor='left')
    return out


def pill(cx, cy, s, color, small=False, anchor="middle"):
    size = 24 if small else 30
    w = len(s) * size * 0.56 + (26 if small else 38)
    h = 42 if small else 58
    if anchor == "left":
        cx += w / 2
    return (f"<rect x='{cx - w / 2}' y='{cy - h / 2}' width='{w}' height='{h}' rx='{h / 2}' fill='{color}'/>"
            + text(cx, cy + size * 0.36, s, size, 700, "white", "middle"))


COLS = [280, 370, 460, 550]
SCORE_X, GUESS_X = 905, 1265
LIGHT = "#d8dee9"


def fmt(v, sign=False):
    return (f"+{v:g}" if sign and v > 0 else f"{v:g}").replace("-", "&#8722;")


def chip(cx, cy, w):
    return (f"<rect x='{cx - 40}' y='{cy - 28}' width='80' height='56' rx='10' fill='{INK}'/>"
            + text(cx, cy + 11, fmt(w, True), 28, 700, SPAM if w > 0 else LIGHT, "middle"))


def header(y, score=True):
    out = "".join(text(x, y, n(k + 1), 30, 700, SLATE, "middle") for k, x in enumerate(COLS))
    if score:
        out += text(SCORE_X, y, "score", 24, 700, SLATE, "middle") + text(GUESS_X, y, "guess", 24, 700, SLATE, "middle")
    return out + f"<line x1='20' y1='{y + 18}' x2='1340' y2='{y + 18}' stroke='{LIGHT}' stroke-width='3'/>"


def row_label(y, title, sub=None):
    return text(20, y + (0 if sub else 10), title, 28, 700, INK) + (text(20, y + 34, sub, 22, 400, SLATE) if sub else "")


def weight_cells(y, weights):
    return "".join(chip(x, y, w) for x, w in zip(COLS, weights))


def value_cells(y, values, sign=False):
    return "".join(text(x, y + 11, fmt(v, sign), 32, 400, INK, "middle") for x, v in zip(COLS, values))


def calc(values, weights):
    groups = [f"(<tspan font-weight='700'>{fmt(w)}</tspan>&#215;{fmt(v)})" for v, w in zip(values, weights)]
    total = round(sum(v * w for v, w in zip(values, weights)), 2)
    return " + ".join(groups), total


def score_cell(y, values, weights):
    expr, total = calc(values, weights)
    return text(SCORE_X, y + 10, f"{expr} = <tspan font-weight='700'>{fmt(total)}</tspan>", 25, 400, INK, "middle"), total


def guess_cell(y, total, right=None, sure=None):
    out = pill(GUESS_X, y, "Spam" if total > 0 else "Not spam", SPAM if total > 0 else REAL, small=True)
    if sure:
        out += text(GUESS_X, y + 52, f"{sure}% sure", 26, 700, INK, "middle")
    if right is not None:
        out += tick(GUESS_X + 100, y) if right else cross(GUESS_X + 100, y)
    return out


PERFECT = [1, 1, -1, -1]


def weights_slide():
    terms = " + ".join(f"({fmt(w)} &#215; {n(k + 1)})" for k, w in enumerate(PERFECT))
    parts = [text(680, 40, f"score = {terms}", 34, 700, INK, "middle"), header(130),
             row_label(215, "Weights", "the model"), weight_cells(215, PERFECT)]
    for y, name, values in [(320, "Email A", [1, 1, 0, 0]), (420, "Email B", [0, 0, 1, 1])]:
        cell, total = score_cell(y, values, PERFECT)
        parts += [row_label(y, name), value_cells(y, values), cell, guess_cell(y, total)]
    return svg(1360, 470, parts)


def nudge():
    email, before = [1, 1, 0, 0], [0, -1, 0, -1]
    after = [w + v for w, v in zip(before, email)]
    old_cell, old = score_cell(320, email, before)
    new_cell, new = score_cell(520, email, after)
    parts = [header(130, score=False), text(SCORE_X, 130, "score", 24, 700, SLATE, "middle"),
             text(GUESS_X, 130, "guess", 24, 700, SLATE, "middle"),
             row_label(215, "The email", "labeled Spam"), value_cells(215, email),
             row_label(320, "Weights before"), weight_cells(320, before), old_cell, guess_cell(320, old, right=False),
             row_label(420, "Nudge", "add its numbers"), value_cells(420, email, sign=True),
             row_label(520, "Weights after"), weight_cells(520, after), new_cell, guess_cell(520, new, right=True),
             text(20, 615, "It should have scored higher, so each number is added to its weight. Zeros stay put.", 26, 400, SLATE)]
    return svg(1400, 640, parts, top=100)


def tick(cx, cy):
    return (f"<path d='M{cx - 16},{cy + 2} L{cx - 4},{cy + 15} L{cx + 18},{cy - 14}' fill='none' stroke='#3b7d4a' "
            f"stroke-width='7' stroke-linecap='round' stroke-linejoin='round'/>")


def cross(cx, cy):
    return (f"<path d='M{cx - 13},{cy - 13} L{cx + 13},{cy + 13} M{cx + 13},{cy - 13} L{cx - 13},{cy + 13}' "
            f"stroke='#b4412f' stroke-width='7' stroke-linecap='round'/>")


def node(cx, cy, title, sub):
    return (f"<rect x='{cx - 165}' y='{cy - 58}' width='330' height='116' rx='18' fill='{FROST}' stroke='{INK}' stroke-width='4'/>"
            + text(cx, cy - 8, title, 34, 700, INK, "middle") + text(cx, cy + 32, sub, 24, 400, SLATE, "middle"))


def arrow(x1, y1, x2, y2, color=SLATE):
    a = math.atan2(y2 - y1, x2 - x1)
    tip = lambda r, da: (x2 - r * math.cos(a + da), y2 - r * math.sin(a + da))
    (lx, ly), (rx, ry) = tip(26, 0.55), tip(26, -0.55)
    return (f"<line x1='{x1}' y1='{y1}' x2='{x2 - 14 * math.cos(a):.1f}' y2='{y2 - 14 * math.sin(a):.1f}' stroke='{color}' stroke-width='7' stroke-linecap='round'/>"
            f"<path d='M{x2},{y2} L{lx:.1f},{ly:.1f} L{rx:.1f},{ry:.1f} z' fill='{color}'/>")


def weight_row(cx, y, weights, caption):
    out = text(cx, y - 44, caption, 24, 400, SLATE, "middle")
    for k, w in enumerate(weights):
        x = cx + (k - 1.5) * 80
        out += f"<rect x='{x - 37}' y='{y - 26}' width='74' height='52' rx='10' fill='{INK}'/>"
        out += text(x, y + 9, fmt(w, True), 24, 700, SPAM if w > 0 else LIGHT, "middle")
    return out


def training_loop():
    parts = [text(110, 120, "Labeled emails", 28, 700, INK, "middle")]
    for k, (tag, color) in enumerate([("Spam", SPAM), ("Not spam", REAL), ("Spam", SPAM)]):
        parts.append(envelope(60, 200 + k * 110, tag, color))
    guess, check, nudge_at = (640, 130), (850, 470), (430, 470)
    parts += [flow(290, 310, 452, 130), head(446, 130),
              arrow(760, 195, 860, 395), arrow(680, 470, 605, 470), arrow(420, 395, 520, 195),
              node(*guess, "1  Guess", "score it with the weights"),
              node(*check, "2  Check", "was the guess right?"),
              node(*nudge_at, "3  Nudge", "if wrong, tweak each weight"),
              text(640, 600, "repeat for every email, many times", 26, 400, SLATE, "middle")]
    parts += [text(1215, 120, "Weights", 28, 700, INK, "middle"),
              weight_row(1215, 230, [0.2, -0.3, 0.1, 0.4], "at the start: random"),
              arrow(1215, 290, 1215, 380),
              weight_row(1215, 470, PERFECT, "after training")]
    return svg(1400, 640, parts, top=55)


def inference():
    email = [0.9, 0.8, 0.1, 0.2]
    cell, total = score_cell(320, email, PERFECT)
    sure = round(100 / (1 + math.exp(-total)))
    parts = [header(130), row_label(215, "Weights", "frozen now"), weight_cells(215, PERFECT),
             row_label(320, "A new email"), value_cells(320, email), cell, guess_cell(320, total, sure=sure)]
    return svg(1360, 420, parts, top=90)


def svg(w, h, parts, top=0):
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 {top} {w} {h - top}' width='{w}' height='{h - top}'>{''.join(parts)}</svg>"


def export(name, markup):
    source = OUT / f"{name}_source.svg"
    source.write_text(markup)
    subprocess.run(["rsvg-convert", "-w", "2600", str(source), "-o", str(OUT / f"{name}.png")], check=True)
    subprocess.run(["rsvg-convert", "-f", "svg", str(source), "-o", str(OUT / f"{name}.svg")], check=True)
    source.unlink()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    export("weights", weights_slide())
    export("training_loop", training_loop())
    export("inference", inference())
    export("nudge", nudge())
