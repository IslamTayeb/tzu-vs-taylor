import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import qrcode
from PIL import Image
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).resolve().parent
ROOT, TOOLS, ASSETS, OUT = HERE.parents[1], HERE.parent / "tools", HERE / "assets", HERE / "out"
sys.path[:0] = [str(ROOT), str(TOOLS)]

import plot_style
from tvt import SUN_TZU, TAYLOR, chance_of_taylor, embed, load, quiz, train, traps, word_scores

RED, CYAN, ORANGE, YELLOW, INK, SLATE, SNOW = "#BE616A", "#8FBBBA", "#CF8770", "#EBCB8B", "#2e3440", "#4c566a", "#d8dee9"
COLOR = {TAYLOR: RED, SUN_TZU: CYAN}
LABEL_COLOR = {TAYLOR: RED, SUN_TZU: "#5E9594"}
URL = "https://islamtayeb.github.io/tzu-vs-taylor/"


def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{name}.{ext}", transparent=True)
    plt.close(fig)


def percent_axis(ax, axis="x"):
    ticks = [0, 25, 50, 75, 100]
    getattr(ax, f"set_{axis}lim")(0, 100)
    getattr(ax, f"set_{axis}ticks")(ticks)
    getattr(ax, f"set_{axis}ticklabels")([f"{t}%" for t in ticks])


def split_bar(n_train, n_test):
    fig, ax = plt.subplots(figsize=(12, 2.4))
    ax.barh(0, n_train, color=SNOW, height=0.7, zorder=3)
    ax.barh(0, n_test, left=n_train, color=YELLOW, height=0.7, zorder=3)
    ax.text(n_train / 2, 0, f"{n_train}\nTo Learn From", ha="center", va="center", fontsize=24, fontweight="bold", linespacing=1.3)
    ax.text(n_train + n_test / 2, 0, f"{n_test}\nKept Secret", ha="center", va="center", fontsize=24, fontweight="bold", linespacing=1.3)
    ax.set_xlim(-4, n_train + n_test + 4)
    ax.axis("off")
    save(fig, "split")


def confidence(rounds, p_taylor):
    sure = np.maximum(p_taylor, 1 - p_taylor) * 100
    right = (p_taylor >= 0.5) == (rounds.label == TAYLOR).values
    colors = [ORANGE if not ok else YELLOW if s < 55 else SNOW for s, ok in zip(sure, right)]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(rounds["round"], sure, color=colors, width=0.7, zorder=3)
    for x, s, ok in zip(rounds["round"], sure, right):
        note = "" if ok and s >= 55 else "\nCoin Flip" if ok else "\nMissed"
        ax.text(x, s + 2, f"{s:.0f}%{note}", ha="center", va="bottom", fontsize=17,
                fontweight="bold" if note else "normal")
    percent_axis(ax, "y")
    ax.set_ylim(0, 118)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xticks(rounds["round"])
    ax.tick_params(labelsize=17)
    ax.set_xlabel("Quiz Round", fontsize=19)
    ax.set_ylabel("How Sure The Model Was", fontsize=19)
    save(fig, "confidence")
    return sure, right


def dot_maps(lines, vectors):
    xy = PCA(2, random_state=0).fit_transform(vectors)
    for name, with_line in [("map", False), ("map_line", True)]:
        fig, ax = plt.subplots(figsize=(10, 6.4))
        for who in (SUN_TZU, TAYLOR):
            m = (lines.label == who).values
            ax.scatter(xy[m, 0], xy[m, 1], s=34, color=COLOR[who], alpha=0.85, zorder=3)
            cx, top = xy[m, 0].mean(), xy[:, 1].max()
            ax.text(cx, top + 0.06, who, ha="center", fontsize=26, fontweight="bold", color=LABEL_COLOR[who])
        if with_line:
            flat = LogisticRegression().fit(xy, lines.label)
            (wx, wy), b = flat.coef_[0], flat.intercept_[0]
            ys = np.array([xy[:, 1].min() - 0.05, xy[:, 1].max() + 0.12])
            ax.plot(-(wy * ys + b) / wx, ys, "--", color=INK, lw=3, zorder=4)
        ax.set_ylim(xy[:, 1].min() - 0.05, xy[:, 1].max() + 0.16)
        ax.set_xticks([]); ax.set_yticks([])
        ax.grid(False)
        ax.set_xlabel("Squashed Number 1", fontsize=19)
        ax.set_ylabel("Squashed Number 2", fontsize=19)
        save(fig, name)


def top_words(model, lines, n=8):
    scores = word_scores(model, lines.text)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    for ax, part, who in [(axes[0], scores.head(n), SUN_TZU), (axes[1], scores.tail(n)[::-1], TAYLOR)]:
        values = (part.values if who == TAYLOR else 1 - part.values) * 100
        ax.barh(range(n), values[::-1], color=COLOR[who], height=0.65, zorder=3)
        ax.set_yticks(range(n))
        ax.set_yticklabels(part.index[::-1], fontsize=20)
        percent_axis(ax)
        ax.tick_params(axis="x", labelsize=16)
        ax.set_title(f"Most {who}", fontsize=24, fontweight="bold", color=LABEL_COLOR[who])
    plt.tight_layout(w_pad=4)
    save(fig, "top_words")


def chance_chart(name, labels, percents, truths, height):
    fig, ax = plt.subplots(figsize=(12, height))
    y = np.arange(len(labels))[::-1]
    ax.barh(y, percents, color=[COLOR[t] for t in truths], height=0.62, zorder=3)
    for yy, v in zip(y, percents):
        ax.text(v + 1.5, yy, f"{v:.0f}%", va="center", fontsize=20, fontweight="bold", zorder=5,
                bbox=dict(fc="white", ec="none", pad=1.5))
    ax.axvline(50, color=INK, lw=2, ls="--", zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=18)
    percent_axis(ax)
    ax.tick_params(axis="x", labelsize=16)
    ax.set_xlabel("Model's Chance The Line Is Taylor's", fontsize=19)
    if len(set(truths)) > 1:
        handles = [plt.Rectangle((0, 0), 1, 1, fc=COLOR[w]) for w in (SUN_TZU, TAYLOR)]
        ax.legend(handles, ["Really Sun Tzu", "Really Taylor"], loc="lower center", bbox_to_anchor=(0.5, 1.0),
                  ncol=2, frameon=False, fontsize=18)
    save(fig, name)


def table(name, spec):
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(spec, indent=1))
    subprocess.run([sys.executable, str(TOOLS / "render_table.py"), str(path), str(OUT / f"{name}.png")], check=True)
    path.unlink()


def vector_point():
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([3, 3], [0, 2], "--", color=SLATE, lw=2, zorder=2)
    ax.plot([0, 3], [2, 2], "--", color=SLATE, lw=2, zorder=2)
    ax.scatter([3], [2], s=420, color=ORANGE, zorder=4)
    ax.text(3.18, 2.18, "[3, 2]", fontsize=34, fontweight="bold", zorder=5)
    ax.text(1.5, 0.2, "3 over", ha="center", fontsize=22, color=SLATE)
    ax.text(3.12, 1.0, "2 up", fontsize=22, color=SLATE, va="center")
    ax.set_xlim(0, 5); ax.set_ylim(0, 3.5)
    ax.set_xticks(range(6)); ax.set_yticks(range(4))
    ax.tick_params(labelsize=18)
    save(fig, "vector_point")


def sentence_map():
    sentences = ["My flight got cancelled", "The airline called off our trip", "Our plane never took off",
                 "My dog loves the park", "The puppy chased a ball", "I baked bread this morning", "The cake is in the oven"]
    offsets = [(-16, -16, "right"), (-16, 14, "right"), (16, -34, "left"), (16, 14, "left"), (16, -14, "left"),
               (16, 0, "left"), (16, 0, "left")]
    groups = [SLATE, SLATE, SLATE, ORANGE, ORANGE, YELLOW, YELLOW]
    xy = PCA(2, random_state=0).fit_transform(embed(sentences))
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.scatter(xy[:, 0], xy[:, 1], s=260, color=groups, zorder=4)
    for (x, y), text, (dx, dy, ha) in zip(xy, sentences, offsets):
        ax.annotate(f"\"{text}\"", (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    fontsize=18, zorder=5)
    ax.set_xlim(xy[:, 0].min() - 2.0, xy[:, 0].max() + 1.7)
    ax.set_ylim(xy[:, 1].min() - 0.3, xy[:, 1].max() + 0.35)
    ax.set_xticks([]); ax.set_yticks([])
    ax.grid(False)
    ax.set_xlabel("Squashed Number 1", fontsize=19)
    ax.set_ylabel("Squashed Number 2", fontsize=19)
    save(fig, "sentence_map")


def toy(stage, seed=4):
    rng = np.random.default_rng(seed)
    spam = rng.normal([-1.1, 0.6], 0.55, (40, 2))
    real = rng.normal([1.1, -0.4], 0.55, (40, 2))
    xy, labels = np.vstack([spam, real]), np.array([1] * 40 + [0] * 40)
    flat = LogisticRegression().fit(xy, labels)
    (wx, wy), b = flat.coef_[0], flat.intercept_[0]
    colors = {1: ORANGE, 0: SLATE}

    fig, ax = plt.subplots(figsize=(10, 6))
    fade = 0.25 if stage == 4 else 0.9
    for k, name in [(1, "Spam"), (0, "Not spam")]:
        pts = xy[labels == k]
        ax.scatter(pts[:, 0], pts[:, 1], s=90, color=colors[k], alpha=fade, zorder=3)
        cx, cy = pts.mean(0)
        ax.text(cx, pts[:, 1].max() + 0.35, name, ha="center", fontsize=26, fontweight="bold", color=colors[k], alpha=max(fade, 0.6))
    if stage >= 2:
        ys = np.array([-3, 3])
        ax.plot(-(wy * ys + b) / wx, ys, "--", color=INK, lw=3, zorder=4)
    if stage == 3:
        on_line = -(wy * -0.95 + b) / wx
        for (x, y), dx, ha in [((-2.5, -1.85), 28, "left"), ((on_line, -0.95), -28, "right")]:
            p = flat.predict_proba([[x, y]])[0, 1]
            sure = max(p, 1 - p)
            ax.scatter([x], [y], s=520, color="white", edgecolor=INK, linewidth=3, zorder=6)
            ax.text(x, y, "?", ha="center", va="center", fontsize=24, fontweight="bold", zorder=7)
            note = f"Spam, {min(sure, 0.99):.0%} sure" if sure > 0.6 else f"{sure:.0%} sure: a coin flip"
            ax.annotate(note, (x, y), xytext=(dx, 0), textcoords="offset points", ha=ha, va="center",
                        fontsize=21, fontweight="bold", zorder=7, bbox=dict(fc="white", ec="none", pad=2))
    if stage == 4:
        test = np.array([[-2.2, 1.3], [-1.5, -0.6], [-0.6, 1.6], [-1.8, 0.3], [0.45, 0.2],
                         [2.2, 0.8], [1.6, -1.4], [0.9, 0.6], [2.4, -0.6], [1.0, -1.9]])
        truth = np.array([1] * 5 + [0] * 5)
        guess = flat.predict(test)
        for (x, y), t, g in zip(test, truth, guess):
            ax.scatter([x], [y], s=260, color=colors[t], edgecolor=INK, linewidth=2.5, zorder=6)
            mx, my = x + 0.24, y + 0.2
            if t == g:
                ax.plot([mx - 0.08, mx, mx + 0.16], [my, my - 0.1, my + 0.14], color="#3b7d4a", lw=3.5, zorder=7,
                        solid_capstyle="round")
            else:
                for sign in (1, -1):
                    ax.plot([mx - 0.09, mx + 0.09], [my - 0.09 * sign, my + 0.09 * sign], color="#b4412f", lw=3.5,
                            zorder=7, solid_capstyle="round")
    ax.set_xlim(-3, 3); ax.set_ylim(-2.4, 2.8)
    ax.set_xticks([]); ax.set_yticks([])
    ax.grid(False)
    ax.set_xlabel("Number 1", fontsize=19)
    ax.set_ylabel("Number 2", fontsize=19)
    save(fig, f"toy_{stage}")


def data_rows():
    rows = [("The art of war is of vital importance to the State.", SUN_TZU, "The Art of War, I.1"),
            ("Lately, I've been dressin' for revenge", TAYLOR, "\"Vigilante Shit\" lyric"),
            ("If he is taking his ease, give him no rest.", SUN_TZU, "The Art of War, I.23"),
            ("I respond to extreme pain with defiance.", TAYLOR, "TIME interview, 2023")]
    table("data_rows", {"columns": ["Who", "Source"], "sections": [{"title": "Four of the 642 lines", "rows": [
        {"label": text, "swatch": COLOR[who], "values": [who, source]} for text, who, source in rows]}]})


def photos():
    taylor = Image.open(ASSETS / "taylor.jpg").convert("RGB").crop((60, 120, 1260, 1620))
    statue = Image.open(ASSETS / "suntzu_statue.jpg").convert("RGB").crop((120, 100, 640, 750))
    taylor.resize((960, 1200), Image.LANCZOS).save(OUT / "photo_taylor.jpg", quality=90)
    statue.resize((960, 1200), Image.LANCZOS).save(OUT / "photo_suntzu.jpg", quality=90)


def main():
    OUT.mkdir(exist_ok=True)
    plot_style.apply()
    lines = load()
    model, accuracy, vectors = train(lines)
    n_test = int(np.ceil(len(lines) * 0.2))

    split_bar(len(lines) - n_test, n_test)
    dot_maps(lines, vectors)
    top_words(model, lines)
    vector_point()
    sentence_map()
    for stage in (1, 2, 3, 4):
        toy(stage)
    data_rows()
    photos()

    t = traps()
    trap_labels = ["\"If my ex leaves a door open,\nyou must rush in.\"",
                   "\"girl, let your plans be dark\nand impenetrable as night...\"",
                   "\"Hold out baits to entice my ex.\nFeign disorder, and crush him.\"",
                   "\"...no point in actively trying\nto defeat your enemies\""]
    trap_p = chance_of_taylor(model, list(t.text)) * 100
    chance_chart("traps", trap_labels, trap_p, [TAYLOR if l == TAYLOR else SUN_TZU for l in t.label], 5)

    verse = "If the enemy leaves a door open, you must rush in."
    flip_p = chance_of_taylor(model, [verse, verse.replace("the enemy", "my ex")]) * 100
    chance_chart("flip", ["\"If the enemy leaves\na door open...\"", "\"If my ex leaves\na door open...\""],
                 flip_p, [SUN_TZU, SUN_TZU], 3.4)

    rounds = quiz()
    sure, right = confidence(rounds, chance_of_taylor(model, list(rounds.text)))

    qrcode.make(URL, border=1).convert("RGB").save(OUT / "qr.png")
    facts = {"n_each": len(lines) // 2, "n_test": n_test, "right": round(accuracy * n_test),
             "trap_p": [round(float(x)) for x in trap_p], "flip_p": [round(float(x)) for x in flip_p],
             "quiz_sure": [round(float(s)) for s in sure], "quiz_right": [bool(r) for r in right]}
    (OUT / "facts.json").write_text(json.dumps(facts, indent=1))
    print(facts)


if __name__ == "__main__":
    main()
