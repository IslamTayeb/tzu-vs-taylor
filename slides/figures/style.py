import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT = HERE / "out"
sys.path.insert(0, str(HERE.parents[1]))

RED, CYAN, TEAL, YELLOW, ORANGE = "#BE616A", "#8FBBBA", "#4F8584", "#EBCB8B", "#CF8770"
INK, SLATE, SNOW = "#2e3440", "#4c566a", "#eceff4"
COLOR = {"Taylor": RED, "Sun Tzu": CYAN}
TEXT_COLOR = {"Taylor": RED, "Sun Tzu": TEAL}


def apply():
    for font in ("Virgil.ttf", "Lato-Regular.ttf"):
        font_manager.fontManager.addfont(str(ASSETS / font))
    plt.xkcd(scale=0.7, length=140, randomness=2)
    plt.rcParams.update({
        "font.family": "Virgil 3 YOFF", "font.size": 16, "path.effects": [], "axes.grid": False,
        "axes.edgecolor": INK, "axes.linewidth": 1.4, "text.color": INK, "axes.labelcolor": INK,
        "xtick.color": INK, "ytick.color": INK, "hatch.linewidth": 1.4, "svg.fonttype": "path",
    })


def save(fig, name, **kwargs):
    OUT.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.2, transparent=True, **kwargs)
    plt.close(fig)


def hbar(ax, y, width, who, height=0.62):
    ax.barh(y, width, height=height, color="white", edgecolor=COLOR[who], hatch="////", lw=0, zorder=2)
    ax.barh(y, width, height=height, color="none", edgecolor=INK, lw=1.4, zorder=3)


def doodle(ax, who, x, y, size, zorder=5):
    s = size / 44
    point = lambda px, py: (x + (px - 22) * s, y - (py - 22) * s)
    rect = lambda px, py, w, h, **k: Rectangle(point(px, py + h), w * s, h * s, **k)
    line = dict(ec=INK, lw=1.6, zorder=zorder)
    hatched = dict(fc="white", hatch="////", ec=COLOR[who], lw=0, zorder=zorder)
    if who == "Taylor":
        for cx, cy, r in [(22, 33, 10), (22, 21, 7.5)]:
            ax.add_patch(Circle(point(cx, cy), r * s, **hatched))
            ax.add_patch(Circle(point(cx, cy), r * s, fc="none", **line))
        ax.add_patch(Circle(point(22, 28), 2.5 * s, fc="white", **line))
        ax.add_patch(rect(20.5, 3, 3, 15, fc="white", **line))
        ax.add_patch(rect(18.5, 0, 7, 4, fc="white", **line))
    else:
        blade = [point(22, 1), point(25, 7), point(25, 29), point(19, 29), point(19, 7)]
        ax.add_patch(Polygon(blade, **hatched))
        ax.add_patch(Polygon(blade, fc="none", **line))
        ax.add_patch(rect(12, 29, 20, 3.5, fc=INK, **line))
        ax.add_patch(rect(20.5, 33, 3, 7, fc="white", **line))
        ax.add_patch(Circle(point(22, 42), 2 * s, fc="white", **line))
