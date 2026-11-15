import json

import numpy as np
import qrcode
from matplotlib.colors import LinearSegmentedColormap
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

import style
from style import INK, ORANGE, OUT, SLATE, TEXT_COLOR, YELLOW, doodle, hbar, plt, save
from tvt import SUN_TZU, TAYLOR, chance_of_taylor, embed, load, quiz, train, traps, word_scores

URL = "https://islamtayeb.github.io/tzu-vs-taylor/"


def percent_axis(ax, axis="x"):
    getattr(ax, f"set_{axis}ticks")([0, 50, 100])
    getattr(ax, f"set_{axis}ticklabels")(["0%", "50%", "100%"])
    ax.spines[["top", "right"]].set_visible(False)


def stripe():
    v = embed(["Trash takes itself out every single time."])[0]
    fig, ax = plt.subplots(figsize=(11, 1.4))
    ax.imshow(v[None, :], aspect="auto", vmin=-.15, vmax=.15,
              cmap=LinearSegmentedColormap.from_list("v", [INK, "#eceff4", YELLOW]))
    ax.set_yticks([])
    ax.set_xticks([0, 100, 200, 300, 383])
    ax.set_xlabel("number 1 to 384")
    save(fig, "stripe")


def neighbors(lines, vectors, query="My ex is spreading rumors about me"):
    sims = vectors @ embed([query])[0]
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.set_xlim(0, 11); ax.set_ylim(0, 4); ax.axis("off")
    ax.text(0.1, 3.55, f"\"{query}\"", fontsize=22, va="center")
    ax.text(10.9, 3.1, "closeness", fontsize=13, ha="right", color=SLATE)
    for k, j in enumerate(np.argsort(-sims)[:3]):
        y = 2.55 - k * 0.95
        doodle(ax, lines.label[j], 0.45, y, 0.75)
        ax.text(0.95, y, lines.text[j].split(" / ")[0], fontsize=17, va="center", family="Lato")
        ax.text(10.9, y, f"{sims[j]:.2f}", fontsize=17, va="center", ha="right")
    save(fig, "neighbors")


def data_rows():
    rows = [("The art of war is of vital importance to the State.", SUN_TZU, "Art of War, I.1"),
            ("Lately, I've been dressin' for revenge", TAYLOR, "\"Vigilante Shit\" lyric"),
            ("If he is taking his ease, give him no rest.", SUN_TZU, "Art of War, I.23"),
            ("I respond to extreme pain with defiance.", TAYLOR, "TIME interview, 2023")]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.set_xlim(0, 11); ax.set_ylim(0, 4.2); ax.axis("off")
    for k, (text, who, source) in enumerate(rows):
        y = 3.7 - k * 1.0
        doodle(ax, who, 0.45, y, 0.8)
        ax.text(0.95, y + 0.12, text, fontsize=18, va="center", family="Lato")
        ax.text(0.95, y - 0.27, f"{who}, {source}", fontsize=13, va="center", color=SLATE)
    save(fig, "data_rows")


def split_bar(n_train, n_test):
    fig, ax = plt.subplots(figsize=(10, 1.6))
    ax.barh(0, n_train, color="white", edgecolor=SLATE, hatch="..", lw=0, height=0.7)
    ax.barh(0, n_test, left=n_train, color="white", edgecolor=ORANGE, hatch="////", lw=0, height=0.7)
    ax.barh(0, n_train + n_test, color="none", edgecolor=INK, lw=1.6, height=0.7)
    ax.plot([n_train, n_train], [-0.35, 0.35], color=INK, lw=1.6)
    for x, label in [(n_train / 2, f"{n_train} to learn from"), (n_train + n_test / 2, f"{n_test} secret")]:
        ax.text(x, 0, label, ha="center", va="center", fontsize=20, bbox=dict(fc="white", ec="none", pad=2))
    ax.set_xlim(-5, n_train + n_test + 5); ax.set_ylim(-0.6, 0.6); ax.axis("off")
    save(fig, "split")


def dot_maps(lines, vectors):
    xy = PCA(2, random_state=0).fit_transform(vectors)
    for name, with_line in [("map", False), ("map_line", True)]:
        fig, ax = plt.subplots(figsize=(9, 6.2))
        for who in (SUN_TZU, TAYLOR):
            m = (lines.label == who).values
            ax.scatter(xy[m, 0], xy[m, 1], s=26, color=style.COLOR[who], edgecolor=INK, lw=0.4, alpha=.85, zorder=3)
            cx, cy = xy[m].mean(0)
            doodle(ax, who, cx, cy + 0.02, 0.16, zorder=6)
            ax.text(cx, xy[:, 1].min() - 0.03, who, ha="center", fontsize=22, color=TEXT_COLOR[who])
        if with_line:
            flat = LogisticRegression().fit(xy, lines.label)
            (wx, wy), b = flat.coef_[0], flat.intercept_[0]
            ys = np.array([xy[:, 1].min() - 0.05, xy[:, 1].max() + 0.05])
            ax.plot(-(wy * ys + b) / wx, ys, "--", color=INK, lw=2.2, zorder=4)
        ax.set_aspect("equal")
        ax.axis("off")
        save(fig, name)


def top_words(model, lines):
    scores = word_scores(model, lines.text)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
    for ax, part, who in [(axes[0], scores.head(8), SUN_TZU), (axes[1], scores.tail(8)[::-1], TAYLOR)]:
        values = (part.values if who == TAYLOR else 1 - part.values) * 100
        for y, value in enumerate(values[::-1]):
            hbar(ax, y, value, who)
        ax.set_yticks(range(len(part)))
        ax.set_yticklabels(part.index[::-1], fontsize=19)
        ax.set_xlim(0, 100)
        ax.set_title(f"most {who}", fontsize=22, color=TEXT_COLOR[who])
        percent_axis(ax)
    plt.tight_layout()
    save(fig, "top_words")


def chance_chart(name, labels, percents, truths, height=4.2):
    fig, ax = plt.subplots(figsize=(10, height))
    for y, (value, who) in enumerate(zip(percents[::-1], truths[::-1])):
        hbar(ax, y, value, who)
        ax.text(value + 2, y, f"{value:.0f}%", va="center", fontsize=18, bbox=dict(fc="white", ec="none", pad=1))
    ax.axvline(50, color=INK, lw=1.6, ls="--")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels[::-1], fontsize=18)
    ax.set_xlim(0, 100)
    ax.set_xlabel("model's chance it's Taylor")
    percent_axis(ax)
    save(fig, name)


def confidence(rounds, p_taylor):
    sure = np.maximum(p_taylor, 1 - p_taylor) * 100
    right = (p_taylor >= .5) == (rounds.label == TAYLOR).values
    fig, ax = plt.subplots(figsize=(10, 4.2))
    for x, value, ok in zip(rounds["round"], sure, right):
        ax.bar(x, value, color="white", edgecolor=SLATE if ok else ORANGE, hatch=".." if ok else "////", lw=0, width=0.7)
        ax.bar(x, value, color="none", edgecolor=INK, lw=1.4, width=0.7)
        ax.text(x, value + 3, f"{value:.0f}%", ha="center", fontsize=14, color=INK if ok else ORANGE)
    ax.axhline(50, color=INK, lw=1.6, ls="--")
    ax.set_ylim(0, 112)
    ax.set_xticks(rounds["round"])
    ax.set_xlabel("quiz round")
    ax.set_ylabel("how sure it was")
    percent_axis(ax, "y")
    save(fig, "confidence")
    return sure, right


def main():
    style.apply()
    lines = load()
    model, accuracy, vectors = train(lines)
    n_test = int(np.ceil(len(lines) * 0.2))

    stripe()
    neighbors(lines, vectors)
    data_rows()
    split_bar(len(lines) - n_test, n_test)
    dot_maps(lines, vectors)
    top_words(model, lines)

    t = traps()
    trap_p = chance_of_taylor(model, list(t.text)) * 100
    chance_chart("traps", list(t.tag), trap_p, [TAYLOR if l == TAYLOR else SUN_TZU for l in t.label])

    verse = "Let your plans be dark and impenetrable as night, and when you move, fall like a thunderbolt."
    girl_p = chance_of_taylor(model, [verse, "girl, " + verse[0].lower() + verse[1:]]) * 100
    chance_chart("girl", ["Sun Tzu's real line", "same line + \"girl,\""], girl_p, [SUN_TZU, SUN_TZU], height=2.6)

    rounds = quiz()
    sure, right = confidence(rounds, chance_of_taylor(model, list(rounds.text)))

    qrcode.make(URL, border=1).convert("RGB").save(OUT / "qr.png")
    facts = {"n_each": len(lines) // 2, "n_test": n_test, "right": round(accuracy * n_test),
             "rounds": len(rounds), "traps": len(t), "quiz_sure": [round(float(s)) for s in sure],
             "quiz_right": [bool(r) for r in right]}
    (OUT / "facts.json").write_text(json.dumps(facts, indent=1))
    print(facts)


if __name__ == "__main__":
    main()
