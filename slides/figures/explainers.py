import math
import subprocess

from diagram import FROST, INK, OUT, SLATE, flow, head, sketchy, text

SPAM, REAL = "#BE616A", "#4f8584"


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
    return (f"<rect x='{cx - w / 2}' y='{cy - h / 2}' width='{w}' height='{h}' rx='{h / 2}' fill='{color}' data-fill='solid'/>"
            + text(cx, cy + size * 0.36, s, size, 700, "white", "middle"))


COLS = [280, 370, 460, 550]
SCORE_X, GUESS_X = 905, 1265
LIGHT = "#d8dee9"
NEG = "#4f8584"


def fmt(v, sign=False):
    return (f"+{v:g}" if sign and v > 0 else f"{v:g}").replace("-", "&#8722;")


def chip(cx, cy, w):
    return (f"<rect x='{cx - 40}' y='{cy - 28}' width='80' height='56' rx='10' fill='{FROST}' stroke='{INK}' stroke-width='3'/>"
            + text(cx, cy + 11, fmt(w, True), 28, 700, SPAM if w > 0 else NEG, "middle"))


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


def bands(*rows, width=1330):
    return [f"<rect x='8' y='{y - 46}' width='{width}' height='92' fill='{FROST}' data-fill='solid'/>" for y in rows]


def weights_slide():
    terms = " + ".join(f"({fmt(w)} &#215; {n(k + 1)})" for k, w in enumerate(PERFECT))
    parts = bands(215) + [text(680, 40, f"score = {terms}", 34, 700, INK, "middle"), header(130),
             row_label(215, "Weights", "the model"), weight_cells(215, PERFECT)]
    cell, total = score_cell(320, [1, 1, 0, 0], PERFECT)
    parts += [row_label(320, "An email"), value_cells(320, [1, 1, 0, 0]), cell, guess_cell(320, total)]
    return svg(1360, 380, parts)


def nudge():
    email, before = [1, 1, 0, 0], [0, -1, 0, -1]
    after = [w + v for w, v in zip(before, email)]
    old_cell, old = score_cell(320, email, before)
    new_cell, new = score_cell(520, email, after)
    parts = bands(215, 420, width=1360) + [header(130, score=False), text(SCORE_X, 130, "score", 24, 700, SLATE, "middle"),
             text(GUESS_X, 130, "guess", 24, 700, SLATE, "middle"),
             row_label(215, "The email", "labeled Spam"), value_cells(215, email),
             row_label(320, "Weights before"), weight_cells(320, before), old_cell, guess_cell(320, old, right=False),
             row_label(420, "Nudge", "+1 &#215; its number"), nudge_cells(420, email),
             text(SCORE_X, 412, "Score too low, so push up:", 25, 400, INK, "middle"),
             text(SCORE_X, 446, "nudge = <tspan font-weight='700'>+1</tspan> &#215; each number", 25, 400, INK, "middle"),
             row_label(520, "Weights after", "before + nudge"), weight_cells(520, after), new_cell, guess_cell(520, new, right=True),
             text(20, 615, "If the score were too high, the nudge would be &#8722;1 &#215; each number. A 0 means no nudge.", 26, 400, SLATE)]
    return svg(1400, 640, parts, top=100)


def nudge_cells(y, values):
    return "".join(text(x, y - 6, f"+1&#215;{fmt(v)}", 22, 400, SLATE, "middle") + text(x, y + 30, f"= {fmt(v, True)}", 28, 700, INK, "middle")
                   for x, v in zip(COLS, values))


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
        out += f"<rect x='{x - 37}' y='{y - 26}' width='74' height='52' rx='10' fill='{FROST}' stroke='{INK}' stroke-width='3'/>"
        out += text(x, y + 9, fmt(w, True), 24, 700, SPAM if w > 0 else NEG, "middle")
    return out


def training_loop():
    parts = [text(110, 120, "Labeled emails", 28, 700, INK, "middle")]
    for k, (tag, color) in enumerate([("Spam", SPAM), ("Not spam", REAL), ("Spam", SPAM)]):
        parts.append(envelope(60, 190 + k * 100, tag, color))
    guess, check, nudge_at = (640, 130), (900, 510), (380, 510)
    parts += [flow(290, 290, 452, 130), head(446, 130),
              arrow(760, 195, 885, 445), arrow(730, 510, 555, 510), arrow(400, 445, 520, 195),
              node(*guess, "1  Guess", "score it with the weights"),
              node(*check, "2  Check", "was the guess right?"),
              node(*nudge_at, "3  Nudge", "if wrong, tweak weights"),
              weight_row(640, 345, [0.2, -0.3, 0.1, 0.4], "weights: random"),
              weight_row(640, 690, PERFECT, "after many rounds")]
    return svg(1100, 740, parts, top=55)


def inference():
    email = [0.9, 0.8, 0.1, 0.2]
    cell, total = score_cell(320, email, PERFECT)
    sure = round(100 / (1 + math.exp(-total)))
    parts = bands(215) + [header(130), row_label(215, "Weights", "frozen now"), weight_cells(215, PERFECT),
             row_label(320, "A new email"), value_cells(320, email), cell, guess_cell(320, total, sure=sure)]
    return svg(1360, 420, parts, top=90)


PINK, MINT = "#f1d6d9", "#d6e8e7"


def card(x, y, icon, title, sub):
    return (f"<rect x='{x}' y='{y - 60}' width='590' height='120' rx='16' fill='{PINK}' stroke='{INK}' stroke-width='3'/>"
            + icon(x + 70, y) + text(x + 135, y - 6, title, 32, 700, INK) + text(x + 135, y + 32, sub, 24, 400, SLATE))


def album(cx, cy):
    return (f"<circle cx='{cx}' cy='{cy}' r='38' fill='{INK}' data-fill='solid' stroke='{INK}' stroke-width='3'/>"
            f"<circle cx='{cx}' cy='{cy}' r='13' fill='{SPAM}' data-fill='solid' stroke='{INK}' stroke-width='2'/>")


def notes(cx, cy):
    out = ""
    for dx, dy in [(-16, 14), (16, 6)]:
        out += f"<circle cx='{cx + dx}' cy='{cy + dy}' r='10' fill='{INK}' data-fill='solid'/>"
        out += f"<line x1='{cx + dx + 9}' y1='{cy + dy}' x2='{cx + dx + 9}' y2='{cy + dy - 44}' stroke='{INK}' stroke-width='4'/>"
    return out + f"<line x1='{cx - 7}' y1='{cy - 30}' x2='{cx + 25}' y2='{cy - 38}' stroke='{INK}' stroke-width='6'/>"


def bubble(cx, cy):
    return (f"<path d='M{cx - 40},{cy - 30} h80 v48 h-44 l-20,18 v-18 h-16 z' fill='white' stroke='{INK}' stroke-width='3'/>"
            + "".join(f"<line x1='{cx - 28}' y1='{cy - 16 + 14 * i}' x2='{cx + [28, 18][i]}' y2='{cy - 16 + 14 * i}' stroke='{SLATE}' stroke-width='4'/>" for i in range(2)))


def sources(picked):
    rows = [(110, album, "reputation (2017)", "every song on her revenge album"),
            (280, notes, "3 feud songs", "Bad Blood, Mean, Vigilante Shit"),
            (450, bubble, "19 interview quotes", "each checked against the article")]
    parts = []
    for y, icon, title, sub in rows:
        parts += [card(20, y, icon, title, sub), flow(615, y, 760, 280)]
    parts += [head(760, 280),
              f"<rect x='800' y='180' width='280' height='200' fill='{PINK}' stroke='{SPAM}' stroke-width='4'/>",
              text(940, 285, str(picked), 72, 700, SPAM, "middle"),
              text(940, 330, "lines, picked at random", 24, 400, SLATE, "middle")]
    return svg(1100, 540, parts, top=30)


STEPS = [("Words to numbers", "turn text into vectors"), ("Teach a model", "show it labeled examples"),
         ("Test it", "on data it never saw"), ("You vs. the model", "play along")]


def step_card(x, y, k, title, sub, on, dim):
    fill, stroke = (PINK, SPAM) if on else (FROST, INK)
    group = (f"<rect x='{x}' y='{y}' width='345' height='170' fill='{fill}' stroke='{stroke}' stroke-width='{5 if on else 3}'/>"
             f"<circle cx='{x + 42}' cy='{y + 45}' r='24' fill='white' stroke='{INK}' stroke-width='3'/>"
             + text(x + 42, y + 55, str(k), 28, 700, INK, "middle")
             + text(x + 80, y + 56, title, 27, 700, INK) + text(x + 24, y + 125, sub, 24, 400, SLATE))
    return f"<g opacity='0.35'>{group}</g>" if dim else group


def roadmap(current):
    parts = []
    for k, (title, sub) in enumerate(STEPS):
        x = 20 + k * 395
        parts.append(step_card(x, 40, k + 1, title, sub, k + 1 == current, current and k + 1 != current))
        if k < 3:
            parts += [arrow(x + 352, 125, x + 388, 125)]
    return svg(1590, 250, parts)


def recap():
    cards = [("Words become dots", "an embedding is a vector"), ("A model is a line", "weights are its knobs"),
             ("Training nudges it", "guess, check, nudge"), ("A hidden test grades it", "on emails it never saw")]
    parts = []
    for k, (title, sub) in enumerate(cards):
        x, y = 20 + (k % 2) * 620, 30 + (k // 2) * 200
        parts += [f"<rect x='{x}' y='{y}' width='580' height='160' fill='{FROST}' stroke='{INK}' stroke-width='3'/>",
                  text(x + 30, y + 70, title, 36, 700, INK), text(x + 30, y + 118, sub, 28, 400, SLATE)]
    return svg(1240, 420, parts)


def slider(cx, top, bottom, w, label):
    y = top + (bottom - top) * (1 - w) / 2
    return (f"<line x1='{cx}' y1='{top}' x2='{cx}' y2='{bottom}' stroke='{SLATE}' stroke-width='5'/>"
            f"<rect x='{cx - 22}' y='{y - 12}' width='44' height='24' fill='{SPAM if w > 0 else REAL}' stroke='{INK}' stroke-width='3'/>"
            + text(cx, bottom + 40, label, 26, 700, SLATE, "middle"))


def model_box():
    parts = [text(110, 90, "an email's", 26, 400, SLATE, "middle"), text(110, 122, "vector", 26, 400, SLATE, "middle")]
    style = f"stroke='{INK}' stroke-width='4' fill='none'"
    parts += [f"<path d='M78,150 h-12 v240 h12' {style}/>", f"<path d='M142,150 h12 v240 h-12' {style}/>"]
    parts += [text(110, 200 + 55 * i, "&#8226;", 40, 700, INK, "middle") for i in range(4)]
    parts += [flow(175, 270, 245, 270), head(245, 270),
              f"<rect x='285' y='120' width='460' height='300' fill='{FROST}' stroke='{INK}' stroke-width='4'/>",
              text(515, 168, "the model", 34, 700, INK, "middle")]
    parts += [slider(345 + 113 * i, 205, 345, w, f"<tspan font-style='italic'>w</tspan><tspan baseline-shift='sub' font-size='70%'>{i + 1}</tspan>") for i, w in enumerate([0.6, 0.9, -0.5, -0.8])]
    parts += [text(515, 470, "weights = knobs. Training turns them.", 26, 400, SLATE, "middle"),
              flow(750, 270, 815, 270), head(815, 270),
              f"<rect x='850' y='215' width='170' height='110' fill='white' stroke='{INK}' stroke-width='3'/>",
              text(935, 282, "score", 34, 700, INK, "middle"),
              flow(1025, 270, 1080, 190), head(1080, 190), flow(1025, 270, 1080, 350), head(1080, 350),
              pill(1190, 190, "Spam", SPAM), pill(1190, 350, "Not spam", REAL),
              text(1190, 245, "above 0", 22, 400, SLATE, "middle"), text(1190, 405, "below 0", 22, 400, SLATE, "middle")]
    return svg(1320, 500, parts, top=50)


def svg(w, h, parts, top=0):
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 {top} {w} {h - top}' width='{w}' height='{h - top}'>{''.join(parts)}</svg>"


def export(name, markup):
    source = OUT / f"{name}_source.svg"
    source.write_text(sketchy(markup))
    subprocess.run(["rsvg-convert", "-w", "2600", str(source), "-o", str(OUT / f"{name}.png")], check=True)
    subprocess.run(["rsvg-convert", "-f", "svg", str(source), "-o", str(OUT / f"{name}.svg")], check=True)
    source.unlink()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    export("weights", weights_slide())
    export("training_loop", training_loop())
    export("inference", inference())
    export("nudge", nudge())
    export("sources", sources(300))
    export("model_box", model_box())
    export("recap", recap())
    for k in range(5):
        export(f"roadmap_{k}", roadmap(k))
