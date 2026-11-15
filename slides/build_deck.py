import json
import sys
from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path.home() / ".claude/skills/make-slides"))
from deck_tools import body_of, fit_picture, open_deck, write_bullets

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
FONT = "Lato"
INK = RGBColor(0x2E, 0x34, 0x40)
URL = "islamtayeb.github.io/tzu-vs-taylor"

facts = json.loads((FIG / "facts.json").read_text())
right = round(facts["accuracy"] * facts["n_test"])
deck, layouts = open_deck(HERE / "template.pptx")
W, H = deck.slide_width, deck.slide_height


def picture_slide(title, png, note=None, png_only=False):
    if note:
        slide = deck.slides.add_slide(layouts["Title and Content"])
        body = body_of(slide)
        write_bullets(body.text_frame, [(0, [(note, False)])], size=24)
        body.height = Inches(0.8)
        top = Inches(2.5)
    else:
        slide = deck.slides.add_slide(layouts["Title Only"])
        top = Inches(1.6)
    slide.shapes.title.text = title
    fit_picture(slide, str(FIG / png), (Inches(0.6), top, W - Inches(1.2), H - top - Inches(0.4)), f"fig_{Path(png).stem}", png_only=png_only)
    return slide


def bullet_slide(title, items):
    slide = deck.slides.add_slide(layouts["Title and Content"])
    slide.shapes.title.text = title
    write_bullets(body_of(slide).text_frame, items, size=28)


def big_statement(title, subtitle):
    slide = deck.slides.add_slide(layouts["Title Slide"])
    slide.shapes.title.text = title
    slide.placeholders[1].text = subtitle


picture_slide("Taylor Swift or Sun Tzu?", "title.png")
picture_slide("Everything becomes numbers", "diagram_embed.png")
picture_slide("Then numbers become anything", "diagram_full.png")
picture_slide("One line, 384 numbers", "stripe.png", "An AI model reads \"Trash takes itself out every single time.\" and writes down 384 numbers")
picture_slide("Close numbers, close meaning", "neighbors.png", "No shared words needed")
picture_slide("Our data", "data_rows.png",
              f"{facts['n_each']} lines each: The Art of War (1910 translation) vs. Taylor's reputation lyrics and interviews")
picture_slide("Hide some for the test", "split.png", "Like an exam with questions the model has never seen")
picture_slide("Every line as a dot", "map.png", "384 numbers squashed down to 2 so we can look at them")
picture_slide("Training draws the line", "map_line.png", "The model learns where Taylor ends and Sun Tzu begins")
big_statement(f"{right} out of {facts['n_test']}", "right on lines it had never seen")

slide = deck.slides.add_slide(layouts["Title Only"])
slide.shapes.title.text = "Play along"
box = slide.shapes.add_textbox(Inches(0.8), Inches(3.2), Inches(6.8), Inches(1.6))
box.text_frame.word_wrap = True
p = box.text_frame.paragraphs[0]
p.text = URL
p.font.size = Pt(30)
p.font.bold = True
p2 = box.text_frame.add_paragraph()
p2.text = "Guess first, then see what the model thinks"
p2.font.size = Pt(22)
fit_picture(slide, str(FIG / "qr.png"), (Inches(8.2), Inches(1.6), Inches(4.6), Inches(4.6)), "fixed_qr", png_only=True, edge_allowed=True)

big_statement("You vs. the model", "10 rounds, then 4 traps")
picture_slide("What it learned", "top_words.png", "We fed it single words, one at a time")
picture_slide("One word flips it", "girl.png", "Sun Tzu's \"Let your plans be dark and impenetrable as night...\"")
picture_slide("Fooling it", "traps.png", "It learned topics and tone, not authors")
bullet_slide("Anything modern looks like Taylor", [
    (0, [("\"The library closes at midnight\" scores ", False), ("70% Taylor", True)]),
    (0, [("It only knows two worlds: a 1910 translation and a 2017 pop star", False)]),
])
picture_slide("Read the confidence", "confidence.png", "When it was wrong, it was barely sure")
bullet_slide("Where this shows up in reporting", [
    (0, [("Classify: ", True), ("tag thousands of documents or comments", False)]),
    (0, [("Search: ", True), ("find documents that mean the same thing", False)]),
    (0, [("Cluster: ", True), ("sort a document dump into piles", False)]),
    (0, [("Generate: ", True), ("draft, summarize, translate", False)]),
])
bullet_slide("Ask any AI tool", [
    (0, [("What data did it learn from?", False)]),
    (0, [("Was it tested on data it had never seen?", False)]),
    (0, [("What shortcut could it be using?", False)]),
])

for slide in deck.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    run.font.name = FONT
                    run.font.color.rgb = INK

deck.save(HERE / "tzu_vs_taylor_lecture.pptx")
print(len(deck.slides), "slides")
