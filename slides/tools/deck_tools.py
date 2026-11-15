"""Helpers for building a deck on a theme: bullets, pictures with SVG originals, and the template's own geometry."""
import os

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.util import Emu, Pt

from check_clipping import touches_edge

SVG_EXTENSION = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
SVG_NAMESPACE = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
DRAWING_NAMESPACE = "http://schemas.openxmlformats.org/drawingml/2006/main"
RELATIONSHIP_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def open_deck(path):
    """Open a template or existing deck, returning it with a name-to-layout lookup."""
    deck = Presentation(path)
    return deck, {layout.name: layout for layout in deck.slide_layouts}


def body_of(slide):
    """Return the slide's main text placeholder."""
    return next(shape for shape in slide.placeholders if shape.placeholder_format.idx == 1)


def write_bullets(frame, items, size=None):
    """Replace a text frame with (level, [(text, bold), ...]) items."""
    frame.clear()
    for number, (level, runs) in enumerate(items):
        paragraph = frame.paragraphs[0] if number == 0 else frame.add_paragraph()
        paragraph.level = level
        for text, bold in runs:
            run = paragraph.add_run()
            run.text = text
            run.font.bold = bold or None
            if size:
                run.font.size = Pt(size - 2 * level)


def attach_svg(slide, picture, svg_path):
    """Give a picture its vector original: PowerPoint shows the SVG, other viewers the PNG beside it."""
    package = slide.part.package
    number = sum(1 for part in package.iter_parts() if str(part.partname).startswith("/ppt/media/vector")) + 1
    with open(svg_path, "rb") as handle:
        part = Part(PackURI(f"/ppt/media/vector{number}.svg"), "image/svg+xml", package, handle.read())
    relationship = slide.part.relate_to(part, RELATIONSHIP_TYPE.IMAGE)
    blip = picture._element.xpath(".//a:blip")[0]
    extensions = etree.SubElement(blip, f"{{{DRAWING_NAMESPACE}}}extLst")
    extension = etree.SubElement(extensions, f"{{{DRAWING_NAMESPACE}}}ext", uri=SVG_EXTENSION)
    etree.SubElement(extension, f"{{{SVG_NAMESPACE}}}svgBlip", nsmap={"asvg": SVG_NAMESPACE}).set(f"{{{RELATIONSHIP_NAMESPACE}}}embed", relationship)


def fit_picture(slide, png_path, box, name, png_only=False, edge_allowed=False):
    """Add a figure inside box (left, top, width, height in EMU), using the SVG beside the PNG."""
    svg_path = png_path.rsplit(".", 1)[0] + ".svg"
    if not png_only and not os.path.exists(svg_path):
        raise FileNotFoundError(f"{svg_path} is missing; save the SVG or pass png_only=True for this figure")
    edges = [] if edge_allowed else touches_edge(png_path)
    if edges:
        raise ValueError(f"{png_path} touches its {', '.join(edges)} edge; add margin or pass edge_allowed=True")
    left, top, width, height = box
    pixel_width, pixel_height = Image.open(png_path).size
    scale = min(width / pixel_width, height / pixel_height)
    shown_width, shown_height = int(pixel_width * scale), int(pixel_height * scale)
    picture = slide.shapes.add_picture(png_path, Emu(left + (width - shown_width) // 2), Emu(top + (height - shown_height) // 2), Emu(shown_width), Emu(shown_height))
    picture.name = name
    if not png_only:
        attach_svg(slide, picture, svg_path)
    return picture


def body_box(slide):
    """Return the (left, top, width, height) of the slide's main text placeholder from its layout."""
    body = body_of(slide)
    return body.left, body.top, body.width, body.height
