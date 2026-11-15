"""Center each slide's figure between the bottom of its rendered text and the top of the theme's logo."""
import glob
import io
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.util import Inches

ROMERO_LOGO_TOP = 6.73
MARGIN = 0.92
GAP = 0.14
BAND = 0.25
BALANCE = 0.5
MAX_SHIFT = 0.25
TITLE_DROP = 0.13
DPI = 80
HERE = os.path.dirname(os.path.abspath(__file__))


def pictures_of(slide):
    return [shape for shape in slide.shapes if shape.shape_type == 13 and not shape.name.startswith("fixed_")]


def render_text_only(path, directory):
    """Render a copy of the deck with its pictures removed, returning one image per slide."""
    deck = Presentation(path)
    for slide in deck.slides:
        for picture in [shape for shape in slide.shapes if shape.shape_type == 13]:
            picture._element.getparent().remove(picture._element)
    copy = os.path.join(directory, "text_only.pptx")
    deck.save(copy)
    subprocess.run(["bash", os.path.join(HERE, "render_deck.sh"), copy, directory], check=True, stdout=subprocess.DEVNULL)
    return sorted(glob.glob(os.path.join(directory, "slide-*.jpg")))


def text_span(image_path, logo_top):
    """Return the highest and lowest inked rows, in inches, above the logo and inside the slide's frame."""
    image = Image.open(image_path).convert("L")
    width = image.size[0]
    box = (int(MARGIN * DPI / 2), int(BAND * DPI), width - int(MARGIN * DPI / 2), int(logo_top * DPI))
    inked = image.crop(box).point(lambda value: 255 if value < 200 else 0).getbbox()
    return (BAND, BAND) if inked is None else (BAND + inked[1] / DPI, BAND + inked[3] / DPI)


def is_title_slide(slide):
    return any(shape.placeholder_format.type == PP_PLACEHOLDER.CENTER_TITLE for shape in slide.placeholders)


def place_title(slide, image, slide_height, logo_top):
    """Center a Title Slide's text; with a subtitle, sit just below center, since the large title carries the weight."""
    empty = [shape for shape in slide.placeholders if shape.has_text_frame and not shape.text_frame.text.strip()]
    for shape in empty:
        shape._element.getparent().remove(shape._element)
    has_subtitle = len(list(slide.placeholders)) > 1
    top, bottom = text_span(image, logo_top)
    shift = Inches(slide_height / 914400 / 2 + (TITLE_DROP if has_subtitle else 0) - (top + bottom) / 2)
    for shape in slide.placeholders:
        left, top_edge, width, height = shape.left, shape.top, shape.width, shape.height
        shape.left, shape.top, shape.width, shape.height = left, top_edge + shift, width, height


def ink_center(picture):
    """Return where a picture's visual weight sits, as fractions of its width and height."""
    image = Image.open(io.BytesIO(picture.image.blob)).convert("RGBA")
    flat = Image.new("RGBA", image.size, "white")
    flat.alpha_composite(image)
    ink = flat.convert("L").point(lambda value: 0 if value > 243 else 255 - value)
    columns = ink.resize((400, 1), Image.BOX).tobytes()
    rows = ink.resize((1, 400), Image.BOX).tobytes()
    return sum(i * v for i, v in enumerate(columns)) / sum(columns) / 400, sum(i * v for i, v in enumerate(rows)) / sum(rows) / 400


def balance(picture, slide_width, top, bottom):
    """Nudge a lone picture toward visual balance, by a capped amount that keeps it inside the free space."""
    center_x, center_y = ink_center(picture)
    limit = Inches(MAX_SHIFT)
    shift_x = max(-limit, min(limit, int((0.5 - center_x) * picture.width * BALANCE)))
    shift_y = max(-limit, min(limit, int((0.5 - center_y) * picture.height * BALANCE)))
    margin = Inches(MARGIN / 2)
    picture.left = max(margin, min(slide_width - margin - picture.width, picture.left + shift_x))
    picture.top = max(Inches(top), min(Inches(bottom) - picture.height, picture.top + shift_y))


def place(pictures, slide_width, top, bottom):
    """Scale a lone picture to fill the space, then center the picture or group."""
    left_edge = min(shape.left for shape in pictures)
    right_edge = max(shape.left + shape.width for shape in pictures)
    top_edge = min(shape.top for shape in pictures)
    bottom_edge = max(shape.top + shape.height for shape in pictures)
    height = Inches(bottom - top)
    if len(pictures) == 1:
        shape = pictures[0]
        scale = min(height / shape.height, (slide_width - 2 * Inches(MARGIN)) / shape.width)
        shape.width, shape.height = int(shape.width * scale), int(shape.height * scale)
        left_edge, right_edge, top_edge, bottom_edge = shape.left, shape.left + shape.width, shape.top, shape.top + shape.height
    if bottom_edge - top_edge > height:
        raise ValueError(f"figures need {(bottom_edge - top_edge) / 914400:.2f} in but only {bottom - top:.2f} in is free")
    shift_x = (slide_width - (right_edge - left_edge)) // 2 - left_edge
    shift_y = Inches(top) + (height - (bottom_edge - top_edge)) // 2 - top_edge
    for shape in pictures:
        shape.left, shape.top = shape.left + shift_x, shape.top + shift_y
    if len(pictures) == 1:
        balance(pictures[0], slide_width, top, bottom)


def center_figures(path, logo_top=ROMERO_LOGO_TOP):
    deck = Presentation(path)
    directory = tempfile.mkdtemp()
    try:
        images = render_text_only(path, directory)
        if len(images) != len(deck.slides):
            raise ValueError(f"rendered {len(images)} pages for {len(deck.slides)} slides")
        for number, (slide, image) in enumerate(zip(deck.slides, images), 1):
            pictures = pictures_of(slide)
            if is_title_slide(slide) and not pictures:
                place_title(slide, image, deck.slide_height, logo_top)
            if pictures:
                bottom = text_span(image, logo_top)[1]
                try:
                    place(pictures, deck.slide_width, bottom + GAP, logo_top - GAP)
                except ValueError as error:
                    raise ValueError(f"slide {number}: {error}") from error
    finally:
        shutil.rmtree(directory)
    deck.save(path)


if __name__ == "__main__":
    center_figures(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else ROMERO_LOGO_TOP)
