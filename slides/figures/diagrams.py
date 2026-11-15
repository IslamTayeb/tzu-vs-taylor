import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

import style
from style import ASSETS, CYAN, INK, RED, SLATE, SNOW, YELLOW, doodle, plt, save

TILE_W, TILE_H = 0.115, 0.17
ROWS = [0.70, 0.49, 0.28, 0.07]
OUTPUT_X = 0.71
rng = np.random.default_rng(3)


def tile(fig, x, y):
    ax = fig.add_axes([x, y, TILE_W, TILE_H])
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.08", transform=ax.transAxes,
                                fc=SNOW, ec=SLATE, lw=1.2, clip_on=False, zorder=0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    return ax


def picture(ax, img, extent=(0.06, 0.94, 0.06, 0.94)):
    ax.imshow(img, extent=extent, aspect="auto", zorder=1, interpolation="nearest")


def arrow(fig, start, end):
    fig.add_artist(FancyArrowPatch(start, end, transform=fig.transFigure, arrowstyle="-|>",
                                   mutation_scale=16, color=SLATE, lw=1.4, shrinkA=2, shrinkB=2))


def label(fig, x, y, title, subtitle):
    fig.text(x, y + 0.025, title, fontsize=24, va="bottom")
    fig.text(x, y + 0.005, subtitle, fontsize=17, color=SLATE, va="top")


def wave(ax, x0, width, y0, height, cycles=9):
    t = np.linspace(0, 1, 600)
    w = (np.sin(2 * np.pi * cycles * t) * 0.5 + np.sin(2 * np.pi * 23 * t) * 0.3) * np.exp(-((t - 0.5) ** 2) / 0.06)
    ax.plot(x0 + width * t, y0 + height * w / np.abs(w).max(), color=INK, lw=1.2, zorder=1)


def load_images():
    protein = Image.open(ASSETS / "protein.png").convert("RGBA")
    protein = Image.alpha_composite(Image.new("RGBA", protein.size, SNOW), protein).convert("RGB")
    portrait = Image.open(ASSETS / "suntzu.jpg")
    pixels = portrait.crop((0, 0, portrait.width, portrait.width)).resize((14, 14), Image.BILINEAR)
    return protein, pixels


def inputs(fig, protein, pixels):
    items = [("Proteins", "a chain of amino acids"), ("Language", "words"),
             ("Images", "a grid of pixels"), ("Audio", "a sound wave")]
    axes = [tile(fig, 0.02, y) for y in ROWS]
    picture(axes[0], protein, (0.04, 0.96, 0.04, 0.96))
    axes[1].text(0.5, 0.5, "\"All warfare\nis based on\ndeception.\"", ha="center", va="center", fontsize=16)
    picture(axes[2], pixels)
    wave(axes[3], 0.08, 0.84, 0.5, 0.38)
    for (title, subtitle), y in zip(items, ROWS):
        label(fig, 0.145, y + TILE_H / 2, title, subtitle)


def vectors(fig):
    ax = fig.add_axes([0.40, 0.30, 0.20, 0.38])
    ax.imshow(rng.normal(0, 1, (4, 48)), aspect="auto", vmin=-2, vmax=2,
              cmap=LinearSegmentedColormap.from_list("v", [INK, SNOW, YELLOW]))
    for k in range(1, 4):
        ax.axhline(k - 0.5, color="white", lw=6)
    ax.axis("off")
    fig.text(0.50, 0.71, "Vectors", ha="center", fontsize=26)
    fig.text(0.50, 0.27, "each row is a list of numbers", ha="center", va="top", fontsize=17, color=SLATE)
    for k, y in enumerate(ROWS):
        arrow(fig, (0.335, y + TILE_H / 2), (0.395, 0.30 + 0.38 * (0.875 - 0.25 * k)))


def outputs(fig, protein):
    items = [("Generation", "new text, images, audio, proteins"), ("Classification", "Taylor or Sun Tzu?"),
             ("Search", "find documents that mean the same"), ("Clustering", "sort a pile of documents")]
    axes = [tile(fig, OUTPUT_X, y) for y in ROWS]

    picture(axes[0], protein.transpose(Image.FLIP_LEFT_RIGHT), (0.05, 0.5, 0.42, 0.95))
    axes[0].plot(*np.array([[0.55 + 0.4 * t, 0.68 + 0.18 * np.sin(28 * np.pi * t) * np.exp(-((t - 0.5) ** 2) / 0.05)]
                            for t in np.linspace(0, 1, 300)]).T, color=INK, lw=1, zorder=1)
    axes[0].text(0.5, 0.2, "\"my ex leaves a door open\"", ha="center", va="center", fontsize=11, zorder=1)

    axes[1].set_xlim(0, 2)
    doodle(axes[1], "Taylor", 0.55, 0.5, 0.8)
    doodle(axes[1], "Sun Tzu", 1.45, 0.5, 0.8)

    for k, (width, color) in enumerate([(0.8, INK), (0.6, SLATE), (0.45, SLATE)]):
        axes[2].add_patch(FancyBboxPatch((0.12, 0.68 - k * 0.24), width, 0.12, boxstyle="round,pad=0,rounding_size=0.03",
                                         fc=color, ec="none", alpha=1 - 0.25 * k, zorder=1))

    for color, center in [(RED, 0.32), (CYAN, 0.68)]:
        pts = rng.normal([center, 0.5], 0.09, (22, 2))
        axes[3].scatter(pts[:, 0], pts[:, 1], s=14, color=color, edgecolor=INK, lw=0.3, zorder=1)

    for (title, subtitle), y in zip(items, ROWS):
        label(fig, OUTPUT_X + 0.125, y + TILE_H / 2, title, subtitle)
        arrow(fig, (0.605, 0.49), (OUTPUT_X - 0.005, y + TILE_H / 2))


def embedding_diagrams():
    protein, pixels = load_images()
    for name, full in [("diagram_embed", False), ("diagram_full", True)]:
        fig = plt.figure(figsize=(16, 6.4))
        fig.text(0.16, 0.92, "1. Embedding", ha="center", fontsize=28)
        inputs(fig, protein, pixels)
        vectors(fig)
        if full:
            fig.text(0.83, 0.92, "2. Generation, and more", ha="center", fontsize=28)
            outputs(fig, protein)
        save(fig, name, facecolor="white")


def title():
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.set_xlim(0, 8); ax.set_ylim(0, 3.2); ax.axis("off"); ax.set_aspect("equal")
    doodle(ax, "Taylor", 1.6, 1.6, 2.6)
    doodle(ax, "Sun Tzu", 6.4, 1.6, 2.6)
    ax.text(4, 1.6, "vs", ha="center", va="center", fontsize=40)
    save(fig, "title")


if __name__ == "__main__":
    style.apply()
    title()
    embedding_diagrams()
