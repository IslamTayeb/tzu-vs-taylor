import subprocess

from diagram import FROST, INK, OUT, SLATE, SNOW, YELLOW, flow, head, label, page, text

SPAM, REAL = "#CF8770", "#4c566a"
PICK = "#f6e7c8"


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


def bubble(cx, cy):
    return (f"<path d='M{cx - 56},{cy - 38} h112 a10,10 0 0 1 10,10 v52 a10,10 0 0 1 -10,10 h-70 l-22,20 v-20 h-20 "
            f"a10,10 0 0 1 -10,-10 v-52 a10,10 0 0 1 10,-10 z' fill='white' stroke='{INK}' stroke-width='4' stroke-linejoin='round'/>"
            + "".join(f"<rect x='{cx - 40}' y='{cy - 20 + 18 * i}' width='{[80, 60, 70][i]}' height='7' rx='3.5' fill='{SLATE}'/>" for i in range(3)))


def newspaper(cx, cy):
    x, y = cx - 54, cy - 46
    return (f"<rect x='{x}' y='{y}' width='108' height='92' rx='6' fill='white' stroke='{INK}' stroke-width='4'/>"
            f"<rect x='{x + 12}' y='{y + 12}' width='84' height='16' rx='3' fill='{INK}'/>"
            f"<rect x='{x + 12}' y='{y + 38}' width='36' height='40' fill='{SNOW}' stroke='{SLATE}' stroke-width='2'/>"
            + "".join(f"<rect x='{x + 56}' y='{y + 40 + 12 * i}' width='40' height='5' rx='2.5' fill='{SLATE}'/>" for i in range(4)))


def bin_choice(cx, cy, s, chosen):
    w, h = 230, 70
    fill, stroke = (PICK, YELLOW) if chosen else (FROST, FROST)
    return (f"<rect x='{cx - w / 2}' y='{cy - h / 2}' width='{w}' height='{h}' rx='14' fill='{fill}' stroke='{stroke}' stroke-width='4'/>"
            + text(cx, cy + 11, s, 30, 700 if chosen else 400, INK if chosen else SLATE, "middle"))


def model(cx, cy):
    return (f"<rect x='{cx - 110}' y='{cy - 62}' width='220' height='124' rx='20' fill='{INK}'/>"
            + text(cx, cy + 12, "Model", 36, 700, "white", "middle"))


def examples():
    rows = [(envelope, "An email", ("Spam", "Not spam"), 0),
            (newspaper, "A news story", ("Sports", "Politics"), 1),
            (bubble, "A comment", ("Toxic", "Civil"), 1)]
    parts = []
    for k, (icon, name, (a, b), pick) in enumerate(rows):
        y = 110 + k * 190
        parts += [icon(150, y), text(250, y + 10, name, 32), flow(500, y, 640, y), head(640, y),
                  bin_choice(820, y, a, pick == 0), bin_choice(1100, y, b, pick == 1)]
    return svg(1300, 600, parts)


def learn(stage):
    parts = [text(20, 46, "Learning", 40), text(20, 88, "from labeled examples", 28, 400, SLATE)]
    for k, (tag, color) in enumerate([("Spam", SPAM), ("Not spam", REAL), ("Spam", SPAM)]):
        parts.append(envelope(80, 165 + k * 100, tag, color))
    parts += [flow(330, 265, 520, 265), head(520, 265), text(425, 240, "training", 28, 400, SLATE, "middle"),
              model(670, 265), text(670, 368, "learns the pattern", 28, 400, SLATE, "middle")]
    if stage >= 2:
        y = 590
        parts += [f"<line x1='20' y1='430' x2='1080' y2='430' stroke='{FROST}' stroke-width='4'/>",
                  text(20, 488, "Using it", 40), text(20, 530, "on something new", 28, 400, SLATE),
                  envelope(360, y), text(360, y + 78, "a new email", 28, 400, SLATE, "middle"),
                  flow(425, y, 520, y), head(520, y), model(670, y), flow(785, y, 880, y), head(880, y),
                  pill(990, y - 18, "Spam", SPAM), text(990, y + 50, "87% sure", 34, 700, INK, "middle")]
    return svg(1100, 680, parts)


def svg(w, h, parts):
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}'>{''.join(parts)}</svg>"


def export(name, markup):
    source = OUT / f"{name}_source.svg"
    source.write_text(markup)
    subprocess.run(["rsvg-convert", "-w", "2600", str(source), "-o", str(OUT / f"{name}.png")], check=True)
    subprocess.run(["rsvg-convert", "-f", "svg", str(source), "-o", str(OUT / f"{name}.svg")], check=True)
    source.unlink()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    export("examples", examples())
    export("learn_1", learn(1))
    export("learn_2", learn(2))
