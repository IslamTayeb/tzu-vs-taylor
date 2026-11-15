import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, Polygon, Rectangle

sys.path.insert(0, str(Path.home() / ".claude/skills/make-slides"))
import plot_style

RED, CYAN, YELLOW, ORANGE = "#BE616A", "#8FBBBA", "#EBCB8B", "#CF8770"
NIGHT, SLATE, SNOW, SNOW2 = "#2e3440", "#4c566a", "#e5e9f0", "#eceff4"
TINT = {"Taylor": "#f1d6d9", "Sun Tzu": "#d6e8e7"}
COL = {"Taylor": RED, "Sun Tzu": CYAN}
IMG = Path(__file__).resolve().parents[2] / "docs" / "img"
VIRGIL = Path.home() / ".claude/skills/make-slides/excalidraw/Virgil.ttf"


def apply():
    plot_style.apply()
    font_manager.fontManager.addfont(str(VIRGIL))
    for p in glob.glob(str(Path.home() / "Library/Fonts/Lato-*.ttf")):
        font_manager.fontManager.addfont(p)
    plt.xkcd(scale=0.7, length=140, randomness=2)
    plt.rcParams.update({"font.family": "Virgil 3 YOFF", "path.effects": [], "axes.grid": False,
                         "axes.edgecolor": NIGHT, "axes.linewidth": 1.4, "text.color": NIGHT,
                         "axes.labelcolor": NIGHT, "xtick.color": NIGHT, "ytick.color": NIGHT,
                         "hatch.linewidth": 1.4, "svg.fonttype": "path"})


def hbar(ax, y, width, who, left=0, height=0.62):
    c = COL[who]
    ax.barh(y, width, left=left, height=height, color="white", edgecolor=c, hatch="////", lw=0, zorder=2)
    ax.barh(y, width, left=left, height=height, color="none", edgecolor=NIGHT, lw=1.4, zorder=3)


def doodle(ax, kind, x, y, size, zorder=5):
    s = size / 44
    P = lambda px, py: (x + (px - 22) * s, y - (py - 22) * s)
    kw = dict(ec=NIGHT, lw=1.6, zorder=zorder)
    R = lambda px, py, w, h, **k: Rectangle(P(px, py + h), w * s, h * s, **k)
    if kind == "Taylor":
        for cx, cy, r in [(22, 33, 10), (22, 21, 7.5)]:
            ax.add_patch(Circle(P(cx, cy), r * s, fc="white", hatch="////", **{**kw, "ec": RED, "lw": 0}))
            ax.add_patch(Circle(P(cx, cy), r * s, fc="none", **kw))
        ax.add_patch(Circle(P(22, 28), 2.5 * s, fc="white", **kw))
        ax.add_patch(R(20.5, 3, 3, 15, fc="white", **kw))
        ax.add_patch(R(18.5, 0, 7, 4, fc="white", **kw))
    else:
        blade = [P(22, 1), P(25, 7), P(25, 29), P(19, 29), P(19, 7)]
        ax.add_patch(Polygon(blade, fc="white", hatch="////", **{**kw, "ec": CYAN, "lw": 0}))
        ax.add_patch(Polygon(blade, fc="none", **kw))
        ax.add_patch(R(12, 29, 20, 3.5, fc=NIGHT, **kw))
        ax.add_patch(R(20.5, 33, 3, 7, fc="white", **kw))
        ax.add_patch(Circle(P(22, 42), 2 * s, fc="white", **kw))
