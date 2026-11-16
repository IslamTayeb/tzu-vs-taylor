import json
import re
import subprocess
import sys
from pathlib import Path

from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.dml.color import RGBColor
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
FONT = "Excalifont"


def hand_font():
    theme = deck.slide_masters[0].part.part_related_by(RT.THEME)
    xml = theme.blob.decode()
    xml = re.sub(r'<a:latin typeface="[^"]*"( panose="[^"]*")?/>', f'<a:latin typeface="{FONT}"/>', xml)
    theme._blob = xml.encode()


def figure(title, name, note=None, png_only=False, notes=None):
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
    if notes:
        slide.notes_slide.notes_text_frame.text = notes


def bullets(title, items):
    slide = deck.slides.add_slide(layouts["Title and Content"])
    slide.shapes.title.text = title
    write_bullets(body_of(slide).text_frame, items, size=26)


def statement(title, subtitle=None):
    slide = deck.slides.add_slide(layouts["Title Slide"])
    slide.shapes.title.text = title
    if subtitle:
        slide.placeholders[1].text = subtitle


def textbox(slide, left, top, width, height, lines, center=False, color=None):
    frame = slide.shapes.add_textbox(left, top, width, height).text_frame
    frame.word_wrap = True
    for k, (text, size, bold) in enumerate(lines):
        paragraph = frame.paragraphs[0] if k == 0 else frame.add_paragraph()
        if center:
            paragraph.alignment = 2
        run = paragraph.add_run()
        run.text, run.font.size, run.font.bold = text, Pt(size), bold or None
        if color:
            run.font.color.rgb = RGBColor.from_string(color)


def classes():
    slide = deck.slides.add_slide(layouts["Title Only"])
    slide.shapes.title.text = "Today's Classification Problem"
    pic_h = H - Inches(2.85)
    pic_w = int(pic_h * 0.8)
    for k, (label, photo, color) in enumerate([("Class A: Taylor Swift", "photo_taylor", "A24A53"),
                                               ("Class B: Sun Tzu", "photo_suntzu", "4F8584")]):
        left = W * (1 + 2 * k) // 4 - pic_w // 2
        textbox(slide, left - Inches(0.5), Inches(1.55), pic_w + Inches(1.0), Inches(0.6), [(label, 26, True)], center=True, color=color)
        picture = slide.shapes.add_picture(str(FIGURES / f"{photo}.jpg"), left, Inches(2.2), pic_w, pic_h)
        picture.name = f"fixed_{photo}"
    slide.notes_slide.notes_text_frame.text = CREDIT


def play_along():
    slide = deck.slides.add_slide(layouts["Title Only"])
    slide.shapes.title.text = "Play Along"
    textbox(slide, Inches(0.9), Inches(2.9), Inches(6.6), Inches(2.0),
            [(SHORT_URL, 44, True), (URL, 18, False), ("", 10, False), ("I trained the model.", 24, False),
             ("Let's see how well it does against you.", 24, False)])
    picture = slide.shapes.add_picture(str(FIGURES / "qr.png"), Inches(8.0), Inches(1.7), Inches(4.6), Inches(4.6))
    picture.name = "fixed_qr"


def main():
    facts = json.loads((FIGURES / "facts.json").read_text())
    missed = [i + 1 for i, ok in enumerate(facts["quiz_right"]) if not ok]
    flip = [i + 1 for i, (s, ok) in enumerate(zip(facts["quiz_sure"], facts["quiz_right"])) if ok and s < 55]

    hand_font()
    statement("How Machines Read", "Embeddings and classification")
    figure("What's A Vector?", "vector_point", [("A vector is just a list of numbers. Each number adds a direction", False)])
    figure("Anything Becomes A Vector", "diagram_1")
    for stage in (2, 3, 4, 5):
        figure("Then We Use The Vectors", f"diagram_{stage}")
    figure("Today: Classification", "diagram_6")
    figure("Close Numbers, Close Meaning", "sentence_map",
           [("Each sentence becomes a vector. Similar meanings land close", False)])

    figure("The Model Is A Function", "weights",
           [("Say high n₁, n₂ mean spam and high n₃, n₄ mean not spam", False)])
    figure("Training: Guess, Check, Nudge", "training_loop")
    figure("One Nudge, Up Close", "nudge")
    figure("Every Email Becomes A Dot", "toy_1", [("Each email's vector, squashed down to 2 numbers so we can draw it", False)])
    figure("Hide Some For The Test", "toy_split", [("Hide some emails before training. They are the exam", False)])
    for k, note in enumerate(["After 4 emails", "After 16 emails", "After all 90: the line is where the score is exactly 0"], 1):
        figure("Training Draws A Line", f"toy_train_{k}", [(note, False)])
    figure("Then It Guesses", "inference", [("Same function, new email. A bigger score means a surer guess", False)])
    figure("New Emails Land On A Side", "toy_3", [("Far from the line: sure. Near the line: a coin flip", False)])
    figure("Then We Grade It", "toy_4", [("Test it on the 10 hidden emails: ", False), ("9 of 10 right", True)])

    classes()
    figure("What It Learned From", "data_rows",
           [(f"{facts['n_each']} lines each: ", True), ("The Art of War vs. Taylor's lyrics and interviews", False)])
    figure("Where The Taylor Lines Come From", "sources", [("Songs about enemies, so it isn't too easy", False)])
    n_test = facts["n_test"]
    figure("Hide Some For The Test", "split",
           [(f"Same as the emails: {2 * facts['n_each'] - n_test} to learn from, {n_test} hidden", False)])
    figure("Every Line As A Dot", "map", [("Each line's embedding: 384 numbers, squashed to 2 to draw it", False)])
    figure("Training Draws The Line", "map_line", [("Same function as the emails, now with 384 weights", False)])
    figure(f"{facts['right']} Out Of {n_test} Right", "map_test",
           [("Faded: lines it learned from. Bold: hidden test lines. Circled: misses", False)])

    play_along()

    figure("How Sure It Was", "confidence",
           [(f"It missed {len(missed)} of {len(facts['quiz_right'])}, all close calls", False)])
    figure("Words It Is Most Sure About", "top_words", [("It learned topics, not authors", False)],
           notes=(f"How we got these: we took every word that shows up at least twice in the {2 * facts['n_each']} lines "
                  "and fed each one to the model on its own, as if it were a one-word line. "
                  "The bars are the model's chance for each word. Left: lowest chance of Taylor. Right: highest."))

    a, b = facts["flip_p"]
    figure("Two Words Flip It", "flip",
           [("Swap \"the enemy\" for \"my ex\": ", False), (f"{a}% to {b}% Taylor", True)])
    bullets("Where This Shows Up In Reporting", [
        (0, [("Classify: ", True), ("tag documents", False)]),
        (0, [("Search: ", True), ("find similar stories", False)]),
        (0, [("Cluster: ", True), ("find themes", False)]),
        (0, [("Generate: ", True), ("draft and summarize", False)]),
    ])

    for slide in deck.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = FONT
    deck.save(DECK)
    subprocess.run([sys.executable, str(TOOLS / "center_figures.py"), str(DECK), "7.1"], check=True)
    print(len(deck.slides), "slides")


if __name__ == "__main__":
    main()
