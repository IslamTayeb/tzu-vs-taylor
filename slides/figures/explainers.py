import math
import subprocess

from diagram import FROST, INK, OUT, SLATE, flow, head, text

SPAM, REAL = "#CF8770", "#4c566a"


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


ROW_Y = [215, 290, 365]


def fmt(v, sign=False):
    return (f"+{v:g}" if sign and v > 0 else f"{v:g}").replace("-", "&#8722;")


def bracket(cx, values, title):
    top, bottom = ROW_Y[0] - 45, ROW_Y[-1] + 85
    style = f"stroke='{INK}' stroke-width='4' fill='none'"
    out = (text(cx, 120, title, 28, 700, INK, "middle")
           + f"<path d='M{cx - 46},{top} h-12 v{bottom - top} h12' {style}/><path d='M{cx + 46},{top} h12 v{bottom - top} h-12' {style}/>")
    out += "".join(text(cx, y + 12, fmt(v), 34, 400, INK, "middle") for v, y in zip(values, ROW_Y))
    return out + text(cx, ROW_Y[-1] + 62, "&#8942;", 30, 700, SLATE, "middle")


def weight_box(cx, weights, title):
    top, bottom = ROW_Y[0] - 45, ROW_Y[-1] + 85
    out = (text(cx, 120, title, 28, 700, INK, "middle")
           + f"<rect x='{cx - 75}' y='{top}' width='150' height='{bottom - top}' rx='16' fill='{INK}'/>")
    out += "".join(text(cx, y + 12, fmt(w, True), 34, 700, SPAM if w > 0 else "#d8dee9", "middle") for w, y in zip(weights, ROW_Y))
    return out + text(cx, ROW_Y[-1] + 62, "&#8942;", 30, 700, "#d8dee9", "middle")


def score_line(x, y, total):
    return (f"<line x1='{x - 120}' y1='{y - 52}' x2='{x + 90}' y2='{y - 52}' stroke='{INK}' stroke-width='3'/>"
            + text(x - 20, y, f"Score {fmt(total)}", 38, 700, INK, "middle")
            + text(x - 20, y + 40, "add them up", 24, 400, SLATE, "middle"))


def weights_slide():
    values, weights = [0.9, 0.2, 0.8], [2.0, -1.0, 1.5]
    parts = [function_line(weights), envelope(90, ROW_Y[1]), text(90, ROW_Y[1] + 74, "an email", 26, 400, SLATE, "middle"),
             flow(160, ROW_Y[1], 220, ROW_Y[1]), head(222, ROW_Y[1]),
             bracket(330, values, "Its vector"), text(470, ROW_Y[1] + 12, "&#215;", 44, 400, SLATE, "middle"),
             weight_box(610, weights, "Weights")]
    sums = [round(v * w, 2) for v, w in zip(values, weights)]
    parts += [text(900, 120, "Each pair", 28, 700, INK, "middle")]
    parts += [text(900, y + 12, f"{fmt(v)} &#215; {fmt(w)} = {fmt(p, True)}", 30, 400, INK, "middle")
              for v, w, p, y in zip(values, weights, sums, ROW_Y)]
    parts += [score_line(920, 545, round(sum(sums), 2)),
              flow(1080, 530, 1140, 530), head(1142, 530), pill(1245, 530, "Spam", SPAM),
              text(1245, 590, "score above 0", 24, 400, SLATE, "middle")]
    return svg(1360, 640, parts, top=0)


def function_line(weights, y=40):
    terms = " ".join(f"{'&#8722;' if w < 0 else '+'} {abs(w):g} &#215; number {k + 1}" for k, w in enumerate(weights))
    return text(680, y, f"score = {terms[2:] if weights[0] > 0 else terms} + ...", 34, 700, INK, "middle")


def nudge():
    values, before, step = [0.5, 0.9, 0.4], [0.1, 0.3, -0.2], 0.5
    changes = [round(-step * v, 2) for v in values]
    after = [round(b + c, 2) for b, c in zip(before, changes)]
    old = round(sum(v * w for v, w in zip(values, before)), 2)
    new = round(sum(v * w for v, w in zip(values, after)), 2)
    cols = [(170, "Its number"), (430, "Weight before"), (720, "Nudge"), (1010, "Weight after")]
    rows = [140 + 70 * (k + 1) for k in range(3)]
    parts = [envelope(70, 40), pill(150, 40, "Not spam", REAL, small=True, anchor="left"),
             text(330, 52, f"Old weights score it {fmt(old, True)}: guesses Spam", 30, 400, INK),
             cross(1015, 40)]
    parts += [text(x, 140, h, 26, 700, SLATE, "middle") for x, h in cols]
    parts += [f"<line x1='60' y1='158' x2='1150' y2='158' stroke='{FROST}' stroke-width='3'/>"]
    for v, b, c, a, y in zip(values, before, changes, after, rows):
        parts += [text(170, y + 11, fmt(v), 32, 400, INK, "middle"),
                  weight_chip(430, y, b),
                  text(720, y + 11, f"&#8722;{step:g} &#215; {fmt(v)} = {fmt(c)}", 30, 400, INK, "middle"),
                  weight_chip(1010, y, a)]
    parts += [text(60, 465, "Wrong toward spam, so every weight goes down.", 28, 400, SLATE),
              text(60, 505, "A bigger number gets a bigger nudge.", 28, 400, SLATE),
              envelope(70, 590), pill(150, 590, "Not spam", REAL, small=True, anchor="left"),
              text(330, 602, f"New weights score it {fmt(new)}: guesses Not spam", 30, 400, INK),
              tick(1095, 590)]
    return svg(1180, 650, parts)


def weight_chip(cx, cy, w):
    return (f"<rect x='{cx - 50}' y='{cy - 28}' width='100' height='56' rx='10' fill='{INK}'/>"
            + text(cx, cy + 11, fmt(w, True), 28, 700, SPAM if w > 0 else "#d8dee9", "middle"))


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
        x = cx + (k - 1) * 92
        out += f"<rect x='{x - 42}' y='{y - 28}' width='84' height='56' rx='10' fill='{INK}'/>"
        out += text(x, y + 11, fmt(w, True), 26, 700, SPAM if w > 0 else "#d8dee9", "middle")
    return out


def training_loop():
    parts = [text(110, 120, "Labeled emails", 28, 700, INK, "middle")]
    for k, (tag, color) in enumerate([("Spam", SPAM), ("Not spam", REAL), ("Spam", SPAM)]):
        parts.append(envelope(60, 200 + k * 110, tag, color))
    guess, check, nudge = (640, 130), (850, 470), (430, 470)
    parts += [flow(290, 310, 440, 130), head(445, 130),
              arrow(760, 195, 860, 395), arrow(680, 470, 605, 470), arrow(420, 395, 520, 195),
              node(*guess, "1  Guess", "score it with the weights"),
              node(*check, "2  Check", "was the guess right?"),
              node(*nudge, "3  Nudge", "if wrong, tweak each weight"),
              text(640, 600, "repeat for every email, many times", 26, 400, SLATE, "middle")]
    parts += [text(1215, 120, "Weights", 28, 700, INK, "middle"),
              weight_row(1215, 230, [0.1, 0.3, -0.2], "at the start: random"),
              arrow(1215, 290, 1215, 380),
              weight_row(1215, 470, [2.0, -1.0, 1.5], "after training")]
    return svg(1400, 640, parts, top=55)


def inference():
    values, weights = [0.6, 0.2, 0.6], [2.0, -1.0, 1.5]
    sums = [round(v * w, 2) for v, w in zip(values, weights)]
    total = round(sum(sums), 2)
    sure = round(100 / (1 + math.exp(-total)))
    parts = [envelope(90, ROW_Y[1]), text(90, ROW_Y[1] + 74, "a new email", 26, 400, SLATE, "middle"),
             flow(160, ROW_Y[1], 220, ROW_Y[1]), head(222, ROW_Y[1]),
             bracket(330, values, "Its vector"), text(470, ROW_Y[1] + 12, "&#215;", 44, 400, SLATE, "middle"),
             weight_box(610, weights, "Same weights"),
             text(900, 120, "Each pair", 28, 700, INK, "middle")]
    parts += [text(900, y + 12, f"{fmt(v)} &#215; {fmt(w)} = {fmt(p, True)}", 30, 400, INK, "middle")
              for v, w, p, y in zip(values, weights, sums, ROW_Y)]
    parts += [score_line(920, 545, total),
              flow(1080, 530, 1140, 530), head(1142, 530), pill(1245, 510, "Spam", SPAM),
              text(1245, 580, f"{sure}% sure", 34, 700, INK, "middle")]
    return svg(1360, 640, parts, top=70)


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
