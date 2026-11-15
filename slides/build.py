import json
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
FIGURES = HERE / "figures" / "out"
FONT = "Lato"
INK = RGBColor(0x2E, 0x34, 0x40)
URL = "islamtayeb.github.io/tzu-vs-taylor"


class Deck:
    def __init__(self, template):
        self.prs = Presentation(template)
        self.layouts = {layout.name: layout for layout in self.prs.slide_layouts}
        self.width, self.height = self.prs.slide_width, self.prs.slide_height

    def slide(self, layout, title):
        slide = self.prs.slides.add_slide(self.layouts[layout])
        slide.shapes.title.text = title
        return slide

    def picture(self, slide, name, left, top, width, height):
        path = FIGURES / name
        w, h = Image.open(path).size
        scale = min(width / w, height / h)
        shown_w, shown_h = int(w * scale), int(h * scale)
        slide.shapes.add_picture(str(path), Emu(left + (width - shown_w) // 2), Emu(top + (height - shown_h) // 2),
                                 Emu(shown_w), Emu(shown_h))

    def figure(self, title, name, note=None):
        slide = self.slide("Title and Content" if note else "Title Only", title)
        top = Inches(1.6)
        if note:
            body = slide.placeholders[1]
            body.text = note
            body.height = Inches(0.8)
            top = Inches(2.5)
        margin = Inches(0.6)
        self.picture(slide, name, margin, top, self.width - 2 * margin, self.height - top - Inches(0.4))

    def bullets(self, title, items):
        frame = self.slide("Title and Content", title).placeholders[1].text_frame
        frame.clear()
        for k, runs in enumerate(items):
            paragraph = frame.paragraphs[0] if k == 0 else frame.add_paragraph()
            for text, bold in runs:
                run = paragraph.add_run()
                run.text = text
                run.font.bold = bold or None
                run.font.size = Pt(28)

    def statement(self, title, subtitle):
        self.slide("Title Slide", title).placeholders[1].text = subtitle

    def qr(self, title, lines):
        slide = self.slide("Title Only", title)
        frame = slide.shapes.add_textbox(Inches(0.8), Inches(3.2), Inches(6.8), Inches(1.6)).text_frame
        frame.word_wrap = True
        for k, (text, size) in enumerate(lines):
            paragraph = frame.paragraphs[0] if k == 0 else frame.add_paragraph()
            paragraph.text = text
            paragraph.font.size = Pt(size)
        self.picture(slide, "qr.png", Inches(8.2), Inches(1.6), Inches(4.6), Inches(4.6))

    def save(self, path):
        for slide in self.prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for run in (r for p in shape.text_frame.paragraphs for r in p.runs):
                        run.font.name = FONT
                        run.font.color.rgb = INK
        self.prs.save(path)


def main():
    facts = json.loads((FIGURES / "facts.json").read_text())
    deck = Deck(HERE / "template.pptx")

    deck.figure("Taylor Swift or Sun Tzu?", "title.png")
    deck.figure("Everything becomes numbers", "diagram_embed.png")
    deck.figure("Then numbers become anything", "diagram_full.png")
    deck.figure("One line, 384 numbers", "stripe.png",
                "An AI model reads \"Trash takes itself out every single time.\" and writes down 384 numbers")
    deck.figure("Close numbers, close meaning", "neighbors.png", "No shared words needed")
    deck.figure("Our data", "data_rows.png",
                f"{facts['n_each']} lines each: The Art of War (1910 translation) vs. Taylor's reputation lyrics and interviews")
    deck.figure("Hide some for the test", "split.png", "Like an exam with questions the model has never seen")
    deck.figure("Every line as a dot", "map.png", "384 numbers squashed down to 2 so we can look at them")
    deck.figure("Training draws the line", "map_line.png", "The model learns where Taylor ends and Sun Tzu begins")
    deck.statement(f"{facts['right']} out of {facts['n_test']}", "right on lines it had never seen")

    deck.qr("Play along", [(URL, 30), ("Guess first, then see what the model thinks", 22)])
    deck.statement("You vs. the model", f"{facts['rounds']} rounds")
    deck.figure("How sure it was", "confidence.png", "Round 8 was a coin flip, and it missed the last two")
    deck.figure("What it learned", "top_words.png", "We fed it single words, one at a time")
    deck.figure("One word flips it", "girl.png", "Sun Tzu's \"Let your plans be dark and impenetrable as night...\"")
    deck.figure("Fooling it", "traps.png", "It learned topics and tone, not authors")
    deck.bullets("Anything modern looks like Taylor", [
        [("\"The library closes at midnight\" scores ", False), ("79% Taylor", True)],
        [("It only knows two worlds: a 1910 translation and a 2017 pop star", False)],
    ])
    deck.bullets("Where this shows up in reporting", [
        [("Classify: ", True), ("tag thousands of documents or comments", False)],
        [("Search: ", True), ("find documents that mean the same thing", False)],
        [("Cluster: ", True), ("sort a document dump into piles", False)],
        [("Generate: ", True), ("draft, summarize, translate", False)],
    ])
    deck.bullets("Ask any AI tool", [
        [("What data did it learn from?", False)],
        [("Was it tested on data it had never seen?", False)],
        [("What shortcut could it be using?", False)],
    ])

    deck.save(HERE / "tzu_vs_taylor_lecture.pptx")
    print(len(deck.prs.slides), "slides")


if __name__ == "__main__":
    main()
