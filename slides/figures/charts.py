import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
import numpy as np
import qrcode
from PIL import Image
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).resolve().parent
ROOT, TOOLS, ASSETS, OUT = HERE.parents[1], HERE.parent / "tools", HERE / "assets", HERE / "out"
sys.path[:0] = [str(ROOT), str(TOOLS)]

import plot_style
from tvt import SUN_TZU, TAYLOR, chance_of_taylor, embed, load, quiz, split, train, traps, word_scores

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


def split_bar(n_train, n_test, name="split"):
    fig, ax = plt.subplots(figsize=(12, 2.6))
    ax.barh(0, n_train, color=SNOW, height=0.7, zorder=3)
    ax.barh(0, n_test, left=n_train, color=YELLOW, height=0.7, zorder=3)
    total = n_train + n_test
    ax.text(n_train / 2, 0, str(n_train), ha="center", va="center", fontsize=28, fontweight="bold")
    ax.text(n_train + n_test / 2, 0, str(n_test), ha="center", va="center", fontsize=28, fontweight="bold")
    ax.text(n_train / 2, -0.62, "To learn from", ha="center", va="top", fontsize=24)
    ax.text(total, -0.62, "Hidden for the test", ha="right", va="top", fontsize=24)
    ax.set_ylim(-1.15, 0.4)
    ax.set_xlim(-4, n_train + n_test + 4)
    ax.axis("off")
    save(fig, name)


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


def dot_maps(lines, vectors, model):
    labels = lines.label.values
    train_idx, test_idx, _, _ = split(np.arange(len(lines)), labels)
    sign = 1 if model.classes_[1] == TAYLOR else -1
    w, b = sign * model.coef_[0], sign * model.intercept_[0]
    along = vectors @ w / np.linalg.norm(w)
    rest = vectors - np.outer(along, w / np.linalg.norm(w))
    xy = np.column_stack([along, PCA(1, random_state=0).fit_transform(rest)[:, 0]])
    boundary = -b / np.linalg.norm(w)
    missed = test_idx[model.predict(vectors[test_idx]) != labels[test_idx]]
    pad = 0.03 * (xy[:, 1].max() - xy[:, 1].min())
    for name in ("map", "map_line", "map_test"):
        fig, ax = plt.subplots(figsize=(10, 6.4))
        shown = test_idx if name == "map_test" else train_idx
        for who in (SUN_TZU, TAYLOR):
            if name == "map_test":
                m = train_idx[labels[train_idx] == who]
                ax.scatter(xy[m, 0], xy[m, 1], s=24, color=COLOR[who], alpha=0.15, zorder=2)
            m = shown[labels[shown] == who]
            ax.scatter(xy[m, 0], xy[m, 1], s=70 if name == "map_test" else 34, color=COLOR[who],
                       edgecolor=INK if name == "map_test" else "none", linewidth=1.2, alpha=0.9, zorder=3)
            cx = xy[labels == who, 0].mean()
            ax.text(cx, xy[:, 1].max() + 3 * pad, who, ha="center", fontsize=26, fontweight="bold", color=LABEL_COLOR[who])
        if name != "map":
            ax.plot([boundary, boundary], [xy[:, 1].min() - pad, xy[:, 1].max() + 2 * pad], "--", color=INK, lw=3, zorder=4)
        if name == "map_test":
            ax.scatter(xy[missed, 0], xy[missed, 1], s=700, facecolor="none", edgecolor="#b4412f", linewidth=3.5, zorder=5)
        ax.set_ylim(xy[:, 1].min() - pad, xy[:, 1].max() + 7 * pad)
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
    fig = plt.figure(figsize=(17, 5.4))
    grid = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1.35, 1], wspace=0.22)

    ax = fig.add_subplot(grid[0])
    ax.plot([0, 5], [0, 0], color=INK, lw=2.5, zorder=2)
    ax.scatter([3], [0], s=420, color=ORANGE, zorder=4)
    ax.text(3, 0.55, "[3]", ha="center", fontsize=32, fontweight="bold")
    for t in range(6):
        ax.plot([t, t], [-0.12, 0.12], color=INK, lw=2)
        ax.text(t, -0.45, str(t), ha="center", fontsize=18)
    ax.set_xlim(-0.3, 5.3); ax.set_ylim(-1.6, 1.6)
    ax.axis("off")

    ax = fig.add_subplot(grid[1])
    ax.plot([3, 3], [0, 2], "--", color=SLATE, lw=2, zorder=2)
    ax.plot([0, 3], [2, 2], "--", color=SLATE, lw=2, zorder=2)
    ax.scatter([3], [2], s=420, color=ORANGE, zorder=4)
    ax.text(3, 2.45, "[3, 2]", ha="center", fontsize=32, fontweight="bold", zorder=5)
    ax.set_xlim(0, 5); ax.set_ylim(0, 3.5)
    ax.set_xticks(range(6)); ax.set_yticks(range(4))
    ax.tick_params(labelsize=18)

    ax = fig.add_subplot(grid[2], projection="3d")
    x, y, z = 3, 2, 4
    for xs, ys, zs in [([x, x], [y, y], [0, z]), ([0, x], [y, y], [0, 0]), ([x, x], [0, y], [0, 0])]:
        ax.plot(xs, ys, zs, "--", color=SLATE, lw=2)
    ax.scatter([x], [y], [z], s=420, color=ORANGE, depthshade=False)
    ax.text(x, y, z + 1.1, "[3, 2, 4]", ha="center", fontsize=32, fontweight="bold", zorder=10,
            bbox=dict(facecolor="white", edgecolor="none", pad=2))
    ax.set_xlim(0, 5); ax.set_ylim(0, 5); ax.set_zlim(0, 5)
    ax.set_xticks(range(0, 6)); ax.set_yticks(range(0, 6)); ax.set_zticks(range(0, 6))
    ax.tick_params(labelsize=14, pad=0)
    ax.view_init(elev=18, azim=-58)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((0, 0, 0, 0))
    ax.set_box_aspect(None, zoom=1.12)

    ax = fig.add_subplot(grid[3])
    ax.text(0.5, 0.55, "[3, 2, 4, 1, ...]", ha="center", va="center", fontsize=28, fontweight="bold")
    ax.text(0.5, 0.33, "Same idea,\nwe just can't draw it", ha="center", va="top", fontsize=22, color=SLATE)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")

    for k, title in enumerate(["1D: one number", "2D: two numbers", "3D: three numbers", "4D and up"]):
        left = grid[k].get_position(fig)
        fig.text((left.x0 + left.x1) / 2, 0.93, title, ha="center", fontsize=26, fontweight="bold")
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


def toy_data(seed=4):
    rng = np.random.default_rng(seed)
    spam = rng.normal([-1.1, 0.6], 0.55, (40, 2))
    real = rng.normal([1.1, -0.4], 0.55, (40, 2))
    xy = np.vstack([spam, real])[np.ravel(np.column_stack([np.arange(40), np.arange(40, 80)]))]
    return xy, np.tile([1, 0], 40)


def equation(model):
    (wx, wy), b = model.coef_[0], model.intercept_[0]
    sign = lambda v: "+" if v >= 0 else "\u2212"
    first = f"{wx:.1f}".replace("-", "\u2212")
    return f"score = {first} \u00d7 number 1 {sign(wy)} {abs(wy):.1f} \u00d7 number 2 {sign(b)} {abs(b):.1f}"


def toy_axes(ax):
    ax.set_xlim(-3, 3); ax.set_ylim(-2.4, 2.8)
    ax.set_xticks([]); ax.set_yticks([])
    ax.grid(False)
    ax.set_xlabel("Number 1", fontsize=19)
    ax.set_ylabel("Number 2", fontsize=19)


def toy_line(ax, model):
    (wx, wy), b = model.coef_[0], model.intercept_[0]
    ys = np.array([-3, 3])
    ax.plot(-(wy * ys + b) / wx, ys, "--", color=INK, lw=3, zorder=4)


def toy_training(seen, name):
    xy, labels = toy_data()
    colors = {1: ORANGE, 0: SLATE}
    model = LogisticRegression().fit(xy[:seen], labels[:seen])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(xy[seen:, 0], xy[seen:, 1], s=90, color=SNOW, zorder=2)
    ax.scatter(xy[:seen, 0], xy[:seen, 1], s=110 if seen < 80 else 90, color=[colors[k] for k in labels[:seen]], zorder=3)
    toy_line(ax, model)
    ax.text(0, 3.05, equation(model), ha="center", va="center", fontsize=21, fontweight="bold", zorder=6,
            bbox=dict(fc="white", ec=INK, lw=2, boxstyle="round,pad=0.4"))
    toy_axes(ax)
    ax.set_ylim(-2.4, 3.5)
    save(fig, name)


def toy(stage):
    xy, labels = toy_data()
    flat = LogisticRegression().fit(xy, labels)
    colors = {1: ORANGE, 0: SLATE}

    fig, ax = plt.subplots(figsize=(10, 6))
    fade = 0.25 if stage == 4 else 0.9
    for k, name in [(1, "Spam"), (0, "Not spam")]:
        pts = xy[labels == k]
        ax.scatter(pts[:, 0], pts[:, 1], s=90, color=colors[k], alpha=fade, zorder=3)
        cx = pts[:, 0].mean()
        if stage == 1:
            ax.text(cx, pts[:, 1].max() + 0.35, name, ha="center", fontsize=26, fontweight="bold", color=colors[k])
    if stage >= 2:
        toy_line(ax, flat)
    if stage == 3:
        on_line = -(flat.coef_[0][1] * -0.95 + flat.intercept_[0]) / flat.coef_[0][0]
        for (x, y), dx, ha in [((-2.5, -1.85), 28, "left"), ((on_line, -0.95), -28, "right")]:
            p = flat.predict_proba([[x, y]])[0, 1]
            sure = max(p, 1 - p)
            ax.scatter([x], [y], s=520, color="white", edgecolor=INK, linewidth=3, zorder=6)
            ax.text(x, y, "?", ha="center", va="center_baseline", fontsize=24, fontweight="bold", zorder=7)
            note = f"Spam, {min(sure, 0.99):.0%} sure" if sure > 0.6 else f"{sure:.0%} sure: a coin flip"
            ax.annotate(note, (x, y), xytext=(dx, 0), textcoords="offset points", ha=ha, va="center",
                        fontsize=21, fontweight="bold", zorder=7, bbox=dict(fc="white", ec="none", pad=2))
    if stage == 4:
        test = np.array([[-2.2, 1.3], [-1.5, -0.6], [-0.6, 1.6], [-1.8, 0.3], [0.45, 0.2],
                         [2.2, 0.8], [1.6, -1.4], [0.9, 0.6], [2.4, -0.6], [1.0, -1.9]])
        truth = np.array([1] * 5 + [0] * 5)
        guess = flat.predict(test)
        tick = MplPath([(-0.5, 0.05), (-0.12, -0.4), (0.55, 0.5)], [MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO])
        for (x, y), t, g in zip(test, truth, guess):
            ax.scatter([x], [y], s=260, color=colors[t], edgecolor=INK, linewidth=2.5, zorder=6)
            ok = t == g
            ax.plot([x + 0.26], [y + 0.22], marker=tick if ok else "x", markersize=15 if ok else 12,
                    markeredgewidth=3.5, color="#3b7d4a" if ok else "#b4412f", fillstyle="none", zorder=7)
    toy_axes(ax)
    save(fig, f"toy_{stage}")


def data_rows(n_lines):
    rows = [("The art of war is of vital importance to the State.", SUN_TZU, "The Art of War, I.1"),
            ("Lately, I've been dressin' for revenge", TAYLOR, "\"Vigilante Shit\" lyric"),
            ("If he is taking his ease, give him no rest.", SUN_TZU, "The Art of War, I.23"),
            ("I respond to extreme pain with defiance.", TAYLOR, "TIME interview, 2023")]
    table("data_rows", {"columns": ["Who", "Source"], "sections": [{"title": f"Four of the {n_lines} lines", "rows": [
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
    dot_maps(lines, vectors, model)
    top_words(model, lines)
    vector_point()
    sentence_map()
    for stage in (1, 3, 4):
        toy(stage)
    split_bar(80, 10, "toy_split")
    for k, seen in enumerate([4, 16, 80], 1):
        toy_training(seen, f"toy_train_{k}")
    data_rows(len(lines))
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
             "library_p": round(chance_of_taylor(model, "The library closes at midnight.") * 100),
             "quiz_sure": [round(float(s)) for s in sure], "quiz_right": [bool(r) for r in right]}
    (OUT / "facts.json").write_text(json.dumps(facts, indent=1))
    print(facts)


if __name__ == "__main__":
    main()
