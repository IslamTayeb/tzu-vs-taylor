import json
import sys
from pathlib import Path

import numpy as np
import qrcode
from matplotlib.colors import LinearSegmentedColormap
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
import style
import tvt
from style import COL, CYAN, NIGHT, ORANGE, RED, SLATE, SNOW, TINT, YELLOW, doodle, hbar, plt

style.apply()
URL = "https://islamtayeb.github.io/tzu-vs-taylor/"


def save(fig, name):
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.2, transparent=True)
    plt.close(fig)


def bare(ax):
    ax.axis("off")


tvt.say = lambda *a, **k: None
tvt.load()
tvt.train()
st = tvt.state
df = st["df"]
facts = {"n_each": int((df.label == tvt.TAYLOR).sum()), "n_train": len(st["train"]),
         "n_test": len(st["test"]), "accuracy": float(st["accuracy"])}

v = tvt.embed(["Trash takes itself out every single time."])[0]
fig, ax = plt.subplots(figsize=(11, 1.4))
ax.imshow(v[None, :], aspect="auto", cmap=LinearSegmentedColormap.from_list("g", [NIGHT, "#eceff4", YELLOW]), vmin=-.15, vmax=.15)
ax.set_yticks([])
ax.set_xticks([0, 100, 200, 300, 383])
ax.set_xlabel("number 1 to 384")
save(fig, "stripe")

query = "My ex is spreading rumors about me"
sims = np.vstack(df.vec) @ tvt.embed([query])[0]
top = np.argsort(-sims)[:3]
fig, ax = plt.subplots(figsize=(11, 4))
ax.set_xlim(0, 11); ax.set_ylim(0, 4); bare(ax)
ax.text(0.1, 3.55, f"\"{query}\"", fontsize=22, va="center")
for k, j in enumerate(top):
    y = 2.55 - k * 0.95
    text = df.text.iloc[j].split(" / ")[0]
    doodle(ax, df.label.iloc[j], 0.45, y, 0.75)
    ax.text(0.95, y, text, fontsize=17, va="center", family="Lato")
    ax.text(10.9, y, f"{sims[j]:.2f}", fontsize=17, va="center", ha="right")
ax.text(10.9, 3.1, "closeness", fontsize=13, ha="right", color=SLATE)
save(fig, "neighbors")

rows = [("All warfare is based on deception.", tvt.TZU, "Art of War, I.18"),
        ("Lately, I've been dressin' for revenge", tvt.TAYLOR, "\"Vigilante Shit\" lyric"),
        ("If he is taking his ease, give him no rest.", tvt.TZU, "Art of War, I.23"),
        ("Trash takes itself out every single time.", tvt.TAYLOR, "TIME interview, 2023")]
fig, ax = plt.subplots(figsize=(11, 4.2))
ax.set_xlim(0, 11); ax.set_ylim(0, 4.2); bare(ax)
for k, (text, who, src) in enumerate(rows):
    y = 3.7 - k * 1.0
    doodle(ax, who, 0.45, y, 0.8)
    ax.text(0.95, y + 0.12, text, fontsize=18, va="center", family="Lato")
    ax.text(0.95, y - 0.27, f"{who}, {src}", fontsize=13, va="center", color=SLATE)
save(fig, "data_rows")

n_tr, n_te = facts["n_train"], facts["n_test"]
fig, ax = plt.subplots(figsize=(10, 1.6))
ax.barh(0, n_tr, color="white", edgecolor=SLATE, hatch="..", lw=0, height=0.7)
ax.barh(0, n_te, left=n_tr, color="white", edgecolor=ORANGE, hatch="////", lw=0, height=0.7)
ax.barh(0, n_tr + n_te, color="none", edgecolor=NIGHT, lw=1.6, height=0.7)
ax.plot([n_tr, n_tr], [-0.35, 0.35], color=NIGHT, lw=1.6)
ax.text(n_tr / 2, 0, f"{n_tr} to learn from", ha="center", va="center", fontsize=20,
        bbox=dict(fc="white", ec="none", pad=2))
ax.text(n_tr + n_te / 2, 0, f"{n_te} secret", ha="center", va="center", fontsize=20,
        bbox=dict(fc="white", ec="none", pad=2))
ax.set_xlim(-5, n_tr + n_te + 5); ax.set_ylim(-0.6, 0.6); bare(ax)
save(fig, "split")

X = np.vstack(df.vec)
pca = PCA(2, random_state=0).fit(X)
xy = pca.transform(X)
for name, line in [("map", False), ("map_line", True)]:
    fig, ax = plt.subplots(figsize=(9, 6.2))
    for who in (tvt.TZU, tvt.TAYLOR):
        m = (df.label == who).values
        ax.scatter(xy[m, 0], xy[m, 1], s=26, color=COL[who], edgecolor=NIGHT, lw=0.4, alpha=.85, zorder=3)
        cx, cy = xy[m].mean(0)
        doodle(ax, who, cx, cy + 0.02, 0.16, zorder=6)
        ax.text(cx, xy[:, 1].min() - 0.03, who, ha="center", fontsize=22, color=COL[who] if who == tvt.TAYLOR else "#4f8584")
    if line:
        lr = LogisticRegression().fit(xy, df.label)
        w, b = lr.coef_[0], lr.intercept_[0]
        ys = np.array([xy[:, 1].min() - 0.05, xy[:, 1].max() + 0.05])
        ax.plot(-(w[1] * ys + b) / w[0], ys, "--", color=NIGHT, lw=2.2, zorder=4)
    ax.set_aspect("equal")
    bare(ax)
    save(fig, name)

s = tvt.word_scores().sort_values()
fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
for ax, part, who in [(axes[0], s.head(8), tvt.TZU), (axes[1], s.tail(8)[::-1], tvt.TAYLOR)]:
    vals = (part.values if who == tvt.TAYLOR else 1 - part.values) * 100
    for y, (w, val) in enumerate(zip(part.index[::-1], vals[::-1])):
        hbar(ax, y, val, who)
    ax.set_yticks(range(len(part)))
    ax.set_yticklabels(part.index[::-1], fontsize=19)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0%", "50%", "100%"])
    ax.set_title(f"most {who}", fontsize=22, color=RED if who == tvt.TAYLOR else "#4f8584")
    ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
save(fig, "top_words")


def chance_chart(name, labels, p, truth, figsize=(10, 4.2)):
    fig, ax = plt.subplots(figsize=figsize)
    for y, (val, who) in enumerate(zip(p[::-1], truth[::-1])):
        hbar(ax, y, val, who)
        ax.text(val + 2, y, f"{val:.0f}%", va="center", fontsize=18, bbox=dict(fc="white", ec="none", pad=1))
    ax.axvline(50, color=NIGHT, lw=1.6, ls="--")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels[::-1], fontsize=18)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0%", "50%", "100%"])
    ax.set_xlabel("model's chance it's Taylor")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, name)


traps = st["traps"]
trap_p = tvt.prob_taylor(list(traps.text)) * 100
trap_truth = [tvt.TAYLOR if l == tvt.TAYLOR else tvt.TZU for l in traps.label]
chance_chart("traps", list(traps.tag), trap_p, trap_truth)

orig = "Let your plans be dark and impenetrable as night, and when you move, fall like a thunderbolt."
girl_p = tvt.prob_taylor([orig, "girl, " + orig[0].lower() + orig[1:]]) * 100
chance_chart("girl", ["Sun Tzu's real line", "same line + \"girl,\""], girl_p, [tvt.TZU, tvt.TZU], figsize=(10, 2.6))

q = st["quiz"]
pq = tvt.prob_taylor(list(q.text))
conf = np.maximum(pq, 1 - pq) * 100
right = (pq >= .5) == (q.label == tvt.TAYLOR).values
fig, ax = plt.subplots(figsize=(10, 4.2))
for x, c, r in zip(q["round"], conf, right):
    ax.bar(x, c, color="white", edgecolor=SLATE if r else ORANGE, hatch=".." if r else "////", lw=0, width=0.7)
    ax.bar(x, c, color="none", edgecolor=NIGHT, lw=1.4, width=0.7)
    ax.text(x, c + 3, "right" if r else "wrong", ha="center", fontsize=14, color=NIGHT if r else ORANGE)
ax.axhline(50, color=NIGHT, lw=1.6, ls="--")
ax.set_ylim(0, 112)
ax.set_xticks(q["round"])
ax.set_yticks([0, 50, 100])
ax.set_yticklabels(["0%", "50%", "100%"])
ax.set_xlabel("quiz round")
ax.set_ylabel("how sure it was")
ax.spines[["top", "right"]].set_visible(False)
save(fig, "confidence")

qrcode.make(URL, border=1).convert("RGB").save(HERE / "qr.png")
facts.update(trap_p=[round(float(x)) for x in trap_p], girl_p=[round(float(x)) for x in girl_p],
             quiz_conf=[round(float(c)) for c in conf], quiz_right=[bool(r) for r in right])
(HERE / "facts.json").write_text(json.dumps(facts, indent=1))
print(json.dumps(facts))
