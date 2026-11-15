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
    ax.set_xlim(0, n_train + n_test)
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


def neighbors(lines, vectors, query="My ex is spreading rumors about me"):
    sims = vectors @ embed([query])[0]
    rows = [{"label": lines.text[j].split(" / ")[0], "swatch": COLOR[lines.label[j]], "values": [f"{sims[j]:.2f}"]}
            for j in np.argsort(-sims)[:3]]
    table("neighbors", {"columns": ["Closeness"], "sections": [{"title": f"Closest lines to \"{query}\"", "rows": rows}],
                        "highlight": [{"row": rows[0]["label"], "color": "yellow"}]})


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
    neighbors(lines, vectors)
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
