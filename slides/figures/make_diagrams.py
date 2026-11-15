from pathlib import Path

import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

import style
from style import CYAN, IMG, NIGHT, RED, SLATE, SNOW, SNOW2, plt

style.apply()
HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(3)
TILE_W, TILE_H = 0.115, 0.17
YS = [0.70, 0.49, 0.28, 0.07]
CMAP = plt.matplotlib.colors.LinearSegmentedColormap.from_list("v", [NIGHT, SNOW2, "#EBCB8B"])


def tile(fig, x, y, w=TILE_W, h=TILE_H):
    ax = fig.add_axes([x, y, w, h])
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.08", transform=ax.transAxes,
                                fc=SNOW2, ec=SLATE, lw=1.2, clip_on=False, zorder=0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.grid(False)
    return ax


def show(ax, img, pad=0.08):
    ax.imshow(img, extent=(pad, 1 - pad, pad, 1 - pad), aspect="auto", zorder=1, interpolation="nearest")


def arrow(fig, a, b):
    fig.add_artist(FancyArrowPatch(a, b, transform=fig.transFigure, arrowstyle="-|>", mutation_scale=16,
                                   color=SLATE, lw=1.4, shrinkA=2, shrinkB=2))


def label(fig, x, y, title, sub):
    fig.text(x, y + 0.025, title, fontsize=24, color=NIGHT, va="bottom")
    fig.text(x, y + 0.005, sub, fontsize=17, color=SLATE, va="top")


protein = Image.open(IMG / "protein.png").convert("RGBA")
bg = Image.new("RGBA", protein.size, SNOW2)
protein = Image.alpha_composite(bg, protein).convert("RGB")
pixels = Image.open(IMG / "suntzu_face.jpg").resize((14, 14), Image.BILINEAR)


def inputs(fig):
    ax = tile(fig, 0.02, YS[0]); show(ax, protein, 0.04)
    label(fig, 0.145, YS[0] + TILE_H / 2, "Proteins", "a chain of amino acids")
    ax = tile(fig, 0.02, YS[1])
    ax.text(0.5, 0.5, "\"All warfare\nis based on\ndeception.\"", ha="center", va="center", fontsize=16, color=NIGHT)
    label(fig, 0.145, YS[1] + TILE_H / 2, "Language", "words")
    ax = tile(fig, 0.02, YS[2]); show(ax, pixels)
    label(fig, 0.145, YS[2] + TILE_H / 2, "Images", "a grid of pixels")
    ax = tile(fig, 0.02, YS[3])
    t = np.linspace(0, 1, 600)
    wave = (np.sin(2 * np.pi * 9 * t) * 0.5 + np.sin(2 * np.pi * 23 * t) * 0.3) * np.exp(-((t - 0.5) ** 2) / 0.06)
    ax.plot(0.08 + 0.84 * t, 0.5 + 0.38 * wave / np.abs(wave).max(), color=NIGHT, lw=1.2, zorder=1)
    label(fig, 0.145, YS[3] + TILE_H / 2, "Audio", "a sound wave")


def vectors(fig):
    ax = fig.add_axes([0.40, 0.30, 0.20, 0.38])
    ax.imshow(rng.normal(0, 1, (4, 48)), aspect="auto", cmap=CMAP, vmin=-2, vmax=2)
    for k in range(1, 4):
        ax.axhline(k - 0.5, color="white", lw=6)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.text(0.50, 0.71, "Vectors", ha="center", fontsize=26, color=NIGHT)
    fig.text(0.50, 0.27, "each row is a list of numbers", ha="center", va="top", fontsize=17, color=SLATE)
    for k, y in enumerate(YS):
        arrow(fig, (0.335, y + TILE_H / 2), (0.395, 0.30 + 0.38 * (0.875 - 0.25 * k)))


def outputs(fig):
    X = 0.71
    ax = tile(fig, X, YS[0])
    ax.imshow(protein.transpose(Image.FLIP_LEFT_RIGHT), extent=(0.05, 0.5, 0.42, 0.95), aspect="auto", zorder=1)
    t = np.linspace(0, 1, 300)
    w = np.sin(2 * np.pi * 14 * t) * np.exp(-((t - 0.5) ** 2) / 0.05)
    ax.plot(0.55 + 0.4 * t, 0.68 + 0.18 * w, color=NIGHT, lw=1, zorder=1)
    ax.text(0.5, 0.2, "\"bestie, know your opps\"", ha="center", va="center", fontsize=11, color=NIGHT, zorder=1)
    label(fig, X + 0.125, YS[0] + TILE_H / 2, "Generation", "new text, images, audio, proteins")
    ax = tile(fig, X, YS[1])
    ax.set_xlim(0, 2); ax.set_ylim(0, 1)
    style.doodle(ax, "Taylor", 0.55, 0.5, 0.8)
    style.doodle(ax, "Sun Tzu", 1.45, 0.5, 0.8)
    label(fig, X + 0.125, YS[1] + TILE_H / 2, "Classification", "Taylor or Sun Tzu?")
    ax = tile(fig, X, YS[2])
    for k, (w, c) in enumerate([(0.8, NIGHT), (0.6, SLATE), (0.45, SLATE)]):
        ax.add_patch(FancyBboxPatch((0.12, 0.68 - k * 0.24), w, 0.12, boxstyle="round,pad=0,rounding_size=0.03",
                                    fc=c, ec="none", alpha=1 - 0.25 * k, zorder=1))
    label(fig, X + 0.125, YS[2] + TILE_H / 2, "Search", "find documents that mean the same")
    ax = tile(fig, X, YS[3])
    for c, mx in [(RED, 0.32), (CYAN, 0.68)]:
        pts = rng.normal([mx, 0.5], 0.09, (22, 2))
        ax.scatter(pts[:, 0], pts[:, 1], s=14, color=c, edgecolor=NIGHT, lw=0.3, zorder=1)
    label(fig, X + 0.125, YS[3] + TILE_H / 2, "Clustering", "sort a pile of documents")
    for y in YS:
        arrow(fig, (0.605, 0.49), (X - 0.005, y + TILE_H / 2))


for name, full in [("diagram_embed", False), ("diagram_full", True)]:
    fig = plt.figure(figsize=(16, 6.4))
    fig.text(0.16, 0.92, "1. Embedding", ha="center", fontsize=28, color=NIGHT)
    inputs(fig)
    vectors(fig)
    if full:
        fig.text(0.83, 0.92, "2. Generation, and more", ha="center", fontsize=28, color=NIGHT)
        outputs(fig)
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=300, transparent=False, facecolor="white", bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
