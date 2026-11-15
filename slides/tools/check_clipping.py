"""Fail when a figure's content touches its image edge, which means something was cut off."""
import sys

from PIL import Image, ImageChops


def touches_edge(path, tolerance=8):
    """Return the edges where the image differs from its corner background."""
    image = Image.open(path).convert("RGBA")
    background = Image.new("RGBA", image.size, image.getpixel((0, 0)))
    difference = ImageChops.difference(image, background).convert("L").point(lambda value: 255 if value > tolerance else 0)
    box = difference.getbbox()
    if box is None:
        return []
    width, height = image.size
    left, top, right, bottom = box
    return [name for name, touched in (("left", left == 0), ("top", top == 0), ("right", right == width), ("bottom", bottom == height)) if touched]


if __name__ == "__main__":
    failed = {path: touches_edge(path) for path in sys.argv[1:]}
    failed = {path: edges for path, edges in failed.items() if edges}
    for path, edges in failed.items():
        print(f"{path}: content touches {', '.join(edges)}")
    sys.exit(1 if failed else 0)
