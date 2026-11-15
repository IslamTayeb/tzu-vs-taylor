import json
import subprocess
import sys
from pathlib import Path

from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
TOOLS, FIGURES = HERE / "tools", HERE / "figures" / "out"
sys.path.insert(0, str(TOOLS))
from deck_tools import body_of, fit_picture, open_deck, write_bullets

DECK = HERE / "tzu_vs_taylor_lecture.pptx"
SHORT_URL, URL = "tinyurl.com/tzuvt", "islamtayeb.github.io/tzu-vs-taylor"
CREDIT = "Photos: Glenn Francis (CC BY-SA 4.0); 663highland (CC BY 2.5); Wikimedia Commons"

deck, layouts = open_deck(HERE / "template.pptx")
W, H = deck.slide_width, deck.slide_height


def figure(title, name, note=None, png_only=False):
    if note:
        slide = deck.slides.add_slide(layouts["Title and Content"])
        write_bullets(body_of(slide).text_frame, [(0, note)], size=24)
        top = Inches(2.5)
    else:
        slide = deck.slides.add_slide(layouts["Title Only"])
        top = Inches(1.6)
    slide.shapes.title.text = title
    fit_picture(slide, str(FIGURES / f"{name}.png"), (Inches(0.45), top, W - Inches(0.9), H - top - Inches(0.2)),
                f"fixed_{name}", png_only=png_only)


def bullets(title, items):
    slide = deck.slides.add_slide(layouts["Title and Content"])
    slide.shapes.title.text = title
    write_bullets(body_of(slide).text_frame, items, size=26)


def statement(title, subtitle=None):
    slide = deck.slides.add_slide(layouts["Title Slide"])
    slide.shapes.title.text = title
    if subtitle:
        slide.placeholders[1].text = subtitle


def textbox(slide, left, top, width, height, lines, center=False):
    frame = slide.shapes.add_textbox(left, top, width, height).text_frame
    frame.word_wrap = True
    for k, (text, size, bold) in enumerate(lines):
        paragraph = frame.paragraphs[0] if k == 0 else frame.add_paragraph()
        if center:
            paragraph.alignment = 2
        run = paragraph.add_run()
        run.text, run.font.size, run.font.bold = text, Pt(size), bold or None


def classes():
    slide = deck.slides.add_slide(layouts["Title Only"])
    slide.shapes.title.text = "Today's Classification Problem"
    pic_h = H - Inches(2.85)
    pic_w = int(pic_h * 0.8)
    for k, (label, photo) in enumerate([("Class A: Taylor Swift", "photo_taylor"), ("Class B: Sun Tzu", "photo_suntzu")]):
        left = W * (1 + 2 * k) // 4 - pic_w // 2
        textbox(slide, left - Inches(0.5), Inches(1.55), pic_w + Inches(1.0), Inches(0.6), [(label, 26, True)], center=True)
        picture = slide.shapes.add_picture(str(FIGURES / f"{photo}.jpg"), left, Inches(2.2), pic_w, pic_h)
        picture.name = f"fixed_{photo}"
    textbox(slide, Inches(0.5), H - Inches(0.55), W - Inches(1.0), Inches(0.35), [(CREDIT, 10, False)], center=True)


def play_along():
    slide = deck.slides.add_slide(layouts["Title Only"])
    slide.shapes.title.text = "Play Along"
    textbox(slide, Inches(0.9), Inches(2.9), Inches(6.6), Inches(2.0),
            [(SHORT_URL, 44, True), (URL, 18, False), ("", 10, False), ("Guess first, then see what the model thinks", 24, False)])
    picture = slide.shapes.add_picture(str(FIGURES / "qr.png"), Inches(8.0), Inches(1.7), Inches(4.6), Inches(4.6))
    picture.name = "fixed_qr"


def main():
    facts = json.loads((FIGURES / "facts.json").read_text())
    missed = [i + 1 for i, ok in enumerate(facts["quiz_right"]) if not ok]
    flip = [i + 1 for i, (s, ok) in enumerate(zip(facts["quiz_sure"], facts["quiz_right"])) if ok and s < 55]

    statement("How Machines Read", "Embeddings and classification")
    figure("What's A Vector?", "vector_point", [("A vector is just a list of numbers. Each number adds a direction", False)])
    figure("Embedding: Anything Becomes A Vector", "diagram_1")
    figure("Then We Use The Vectors", "diagram_2")
    figure("Four Ways To Use Them", "diagram_3")
    figure("Close Numbers, Close Meaning", "sentence_map",
           [("Each sentence's embedding is 384 numbers; similar meanings land close", False)])

    figure("What Is Classification?", "examples", [("Sorting each thing into one of a few groups", False)])
    figure("How A Model Learns", "learn_1")
    figure("Then It Guesses", "learn_2")
    figure("Every Email Becomes A Dot", "toy_1", [("Each email's embedding, squashed from 384 numbers to 2 so we can draw it", False)])
    figure("Training Draws A Line", "toy_2", [("Learning means finding the line between the two groups", False)])
    figure("New Emails Land On A Side", "toy_3", [("Far from the line: sure. Near the line: a coin flip", False)])
    figure("Then We Grade It", "toy_4", [("Test it on emails it never saw, like an exam: ", False), ("9 of 10 right", True)])

    classes()
    figure("What It Learned From", "data_rows",
           [(f"{facts['n_each']} lines each: ", True), ("The Art of War (1910) vs. Taylor's lyrics and interviews", False)])
    figure("Hide Some For The Test", "split", [("Same recipe as the emails", False)])
    figure("Every Line As A Dot", "map", [("Each line's embedding, squashed to 2 numbers, just like the emails", False)])
    figure("Training Draws The Line", "map_line", [("Where Taylor ends and Sun Tzu begins", False)])
    statement(f"{facts['right']} Out Of {facts['n_test']}", "right on lines it had never seen. Can you beat it?")

    play_along()

    figure("How Sure It Was", "confidence",
           [(f"Round {flip[0]} was a coin flip; it missed rounds {missed[0]} and {missed[1]}", False)])
    figure("Words It Is Most Sure About", "top_words", [("It learned topics, not authors", False)])

    a, b = facts["flip_p"]
    figure("Two Words Flip It", "flip",
           [("Swap \"the enemy\" for \"my ex\" in a real Sun Tzu verse: ", False), (f"{a}% to {b}% Taylor", True)])
    figure("Fooling It", "traps", [("Small edits fool it; Taylor on enemies reads as Sun Tzu", False)])
    bullets("Anything Modern Looks Like Taylor", [
        (0, [("\"The library closes at midnight.\" scores ", False), ("82% Taylor", True)]),
        (0, [("It only knows two worlds: a 1910 translation and a 2017 pop star", False)]),
    ])
    bullets("Where This Shows Up In Reporting", [
        (0, [("Classify: ", True), ("tag thousands of documents or comments", False)]),
        (0, [("Search: ", True), ("find documents that mean the same thing", False)]),
        (0, [("Cluster: ", True), ("find themes in thousands of comments nobody labeled", False)]),
        (0, [("Generate: ", True), ("draft, summarize, translate", False)]),
    ])
    bullets("Three Questions For Any AI Tool", [
        (0, [("What data did it learn from?", False)]),
        (0, [("Was it tested on data it had never seen?", False)]),
        (0, [("What shortcut could it be using?", False)]),
    ])

    deck.save(DECK)
    subprocess.run([sys.executable, str(TOOLS / "center_figures.py"), str(DECK), "7.1"], check=True)
    print(len(deck.slides), "slides")


if __name__ == "__main__":
    main()
