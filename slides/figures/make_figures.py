import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import qrcode
from matplotlib.colors import LinearSegmentedColormap
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / ".claude/skills/make-slides"))
import plot_style
import tvt

plot_style.apply()
RED, CYAN, YELLOW, ORANGE, NIGHT = "#BE616A", "#8FBBBA", "#EBCB8B", "#CF8770", "#2e3440"
COL = {tvt.TAYLOR: RED, tvt.TZU: CYAN}
URL = "https://islamtayeb.github.io/tzu-vs-taylor/"


def save(fig, name, transparent=True):
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=600, bbox_inches="tight", transparent=transparent)
    plt.close(fig)


tvt.say = lambda *a, **k: None
tvt.load()
tvt.train()
st = tvt.state
facts = {"n_each": int((st["df"].label == tvt.TAYLOR).sum()), "n_train": len(st["train"]),
         "n_test": len(st["test"]), "accuracy": float(st["accuracy"])}

v = tvt.embed(["Trash takes itself out every single time."])[0]
fig, ax = plt.subplots(figsize=(11, 1.3))
cmap = LinearSegmentedColormap.from_list("g", [NIGHT, "#eceff4", YELLOW])
ax.imshow(v[None, :], aspect="auto", cmap=cmap, vmin=-.15, vmax=.15)
ax.set_yticks([])
ax.set_xticks([0, 100, 200, 300, 383])
ax.set_xlabel("Number 1 to 384")
ax.grid(False)
save(fig, "stripe")

counts = [facts["n_train"], facts["n_test"]]
fig, ax = plt.subplots(figsize=(10, 1.6))
ax.barh([0], [counts[0]], color="#d8dee9", edgecolor="black", lw=.6, zorder=3)
ax.barh([0], [counts[1]], left=[counts[0]], color=YELLOW, edgecolor="black", lw=.6, zorder=3)
ax.text(counts[0] / 2, 0, f"{counts[0]} lines to learn from", ha="center", va="center", fontsize=18, zorder=4)
ax.text(counts[0] + counts[1] / 2, 0, f"{counts[1]} kept secret", ha="center", va="center", fontsize=18, zorder=4)
ax.set_xlim(0, sum(counts))
ax.axis("off")
save(fig, "split")

df = st["df"]
X = np.vstack(df.vec)
pca = PCA(2, random_state=0).fit(X)
xy = pca.transform(X)
for name, line in [("map", False), ("map_line", True)]:
    fig, ax = plt.subplots(figsize=(9, 6.5))
    for who in (tvt.TZU, tvt.TAYLOR):
        m = (df.label == who).values
        ax.scatter(xy[m, 0], xy[m, 1], s=22, alpha=.7, color=COL[who], edgecolor="black", lw=.25, label=who, zorder=3)
    if line:
        lr = LogisticRegression().fit(xy, df.label)
        w, b = lr.coef_[0], lr.intercept_[0]
        xs = np.array(ax.get_xlim())
        ax.plot(xs, -(w[0] * xs + b) / w[1], "--", color=NIGHT, lw=2, zorder=4)
        ax.set_xlim(xs)
        ax.set_ylim(xy[:, 1].min() - .05, xy[:, 1].max() + .05)
    ax.legend(frameon=False, loc="upper right", fontsize=16, markerscale=2)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel("Squashed Number A"); ax.set_ylabel("Squashed Number B")
    save(fig, name)

s = tvt.word_scores().sort_values()
fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
for ax, part, who in [(axes[0], s.head(10), tvt.TZU), (axes[1], s.tail(10)[::-1], tvt.TAYLOR)]:
    vals = (part.values if who == tvt.TAYLOR else 1 - part.values) * 100
    ax.barh(part.index[::-1], vals[::-1], color=COL[who], edgecolor="black", lw=.6, zorder=3)
    ax.set_xlim(0, 100)
    ax.set_title(f"Most {who}", fontsize=20)
    ax.set_xlabel(f"Chance Of {who} (%)")
    ax.tick_params(axis="y", labelsize=17)
plt.tight_layout()
save(fig, "top_words")

traps = st["traps"]
tags = list(traps.tag)
p = tvt.prob_taylor(list(traps.text)) * 100
truth = [tvt.TAYLOR if l == tvt.TAYLOR else tvt.TZU for l in traps.label]
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.barh(tags[::-1], p[::-1], color=[COL[t] for t in truth[::-1]], edgecolor="black", lw=.6, zorder=3)
ax.axvline(50, color=NIGHT, lw=1.5, ls="--", zorder=4)
for y, val in enumerate(p[::-1]):
    ax.text(val + 1.5, y, f"{val:.0f}%", va="center", fontsize=16, zorder=5,
            bbox=dict(boxstyle="square,pad=.15", fc="white", ec="none"))
ax.set_xlim(0, 100)
ax.set_xlabel("Model's Chance Of Taylor (%)")
ax.tick_params(axis="y", labelsize=17)
save(fig, "traps")

q = st["quiz"]
pq = tvt.prob_taylor(list(q.text))
conf = np.maximum(pq, 1 - pq) * 100
right = (pq >= .5) == (q.label == tvt.TAYLOR).values
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.bar(q["round"], conf, color=["#d8dee9" if r else ORANGE for r in right], edgecolor="black", lw=.6, zorder=3)
ax.axhline(50, color=NIGHT, lw=1.5, ls="--", zorder=4)
ax.set_ylim(0, 110)
ax.set_xticks(q["round"])
ax.set_xlabel("Quiz Round")
ax.set_ylabel("Model Confidence (%)")
for x, c, r in zip(q["round"], conf, right):
    ax.text(x, c + 2, "Right" if r else "Wrong", ha="center", fontsize=12, zorder=5)
save(fig, "confidence")

img = qrcode.make(URL, border=1).convert("RGB")
img.save(HERE / "qr.png")
facts.update(trap_p=[round(float(x)) for x in p], quiz_conf=[round(float(c)) for c in conf], quiz_right=[bool(r) for r in right])
(HERE / "facts.json").write_text(json.dumps(facts, indent=1))
print(json.dumps(facts))
