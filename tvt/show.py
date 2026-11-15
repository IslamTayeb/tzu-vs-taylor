from html import escape

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import HTML, display
from sklearn.decomposition import PCA

from . import data
from .data import SUN_TZU, TAYLOR
from .model import chance_of_taylor, embed, word_scores

COLORS = {TAYLOR: "#BE616A", SUN_TZU: "#5E9594"}
plt.rcParams.update({"font.size": 16, "axes.titlesize": 20, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 110})

score = {"Class": 0, "Model": 0}
played = set()


def say(html, size=28):
    display(HTML(f'<div style="font-size:{size}px;line-height:1.35;margin:8px 0">{html}</div>'))


def bar(p):
    return HTML(
        f'<div style="display:flex;height:34px;max-width:720px;font-size:18px;color:#fff">'
        f'<div style="width:{p*100:.0f}%;background:{COLORS[TAYLOR]};padding:5px 10px;white-space:nowrap">Taylor {p:.0%}</div>'
        f'<div style="flex:1;background:{COLORS[SUN_TZU]};padding:5px 10px;text-align:right;white-space:nowrap">Sun Tzu {1-p:.0%}</div></div>')


def stripe(text):
    v = embed([text])[0]
    say(f"&ldquo;{escape(text)}&rdquo; &rarr; {len(v)} numbers", 24)
    fig, ax = plt.subplots(figsize=(14, 1.6))
    ax.imshow(v[None, :], aspect="auto", cmap="BrBG", vmin=-.15, vmax=.15)
    ax.set_yticks([])
    ax.set_xlabel("each stripe is one number")
    plt.show()


def closest(lines, vectors, text, k=3):
    sims = vectors @ embed([text])[0]
    say(f"Closest lines to &ldquo;{escape(text)}&rdquo;:", 22)
    for j in np.argsort(-sims)[:k]:
        who = lines.label[j]
        say(f"<span style='color:{COLORS[who]}'>{who}</span> {sims[j]:.2f} &ldquo;{escape(lines.text[j])}&rdquo;", 20)


def accuracy(value, n):
    say(f"Right on <b style='font-size:48px'>{value:.0%}</b> of {n} lines it has never seen")


def verdict(model, text):
    p = chance_of_taylor(model, text)
    guess = TAYLOR if p >= 0.5 else SUN_TZU
    return guess, max(p, 1 - p), p


def scoreboard():
    say("Class <b>{Class}</b> &mdash; Model <b>{Model}</b>".format(**score)
        + f" <span style='color:#999;font-size:18px'>after {len(played)} rounds</span>", 30)


def quiz(model, i):
    q = data.quiz().set_index("round").loc[i]
    say(f"<span style='color:#888'>Round {i}</span><br>&ldquo;{escape(q.text)}&rdquo;", 34)
    vote = {"T": TAYLOR, "S": SUN_TZU}.get(input("Class vote: T or S, then Enter ").strip().upper()[:1])
    guess, sure, p = verdict(model, q.text)
    if i not in played:
        played.add(i)
        score["Class"] += vote == q.label
        score["Model"] += guess == q.label
    say(f"Answer: <b style='color:{COLORS[q.label]}'>{q.label}</b>", 34)
    say(f"Model says <b>{guess}</b>, {sure:.0%} sure {'&#10004;' if guess == q.label else '&#10008;'}", 26)
    display(bar(p))
    scoreboard()


def predict(model, text):
    guess, sure, p = verdict(model, text)
    say(f"&ldquo;{escape(text)}&rdquo; &rarr; <b style='color:{COLORS[guess]}'>{guess}</b>, {sure:.0%} sure", 24)
    display(bar(p))


def traps(model):
    for t in data.traps().itertuples():
        predict(model, t.text)
        say(f"<span style='color:#888'>Really: <b>{t.label}</b> &mdash; {escape(t.note)}</span>", 18)


def top_words(model, lines, n=15):
    s = word_scores(model, lines.text)
    fig, axes = plt.subplots(1, 2, figsize=(14, 0.42 * n + 1.5))
    for ax, part, who in [(axes[0], s.head(n), SUN_TZU), (axes[1], s.tail(n)[::-1], TAYLOR)]:
        values = part.values if who == TAYLOR else 1 - part.values
        ax.barh(part.index[::-1], values[::-1], color=COLORS[who])
        ax.set_xlim(0.5, 1)
        ax.set_title(f"Single words that scream {who}")
    plt.tight_layout()
    plt.show()


def vector_map(lines, vectors):
    pca = PCA(2, random_state=0).fit(vectors)
    xy = pca.transform(vectors)
    fig, ax = plt.subplots(figsize=(11, 8))
    for who in (SUN_TZU, TAYLOR):
        m = (lines.label == who).values
        ax.scatter(xy[m, 0], xy[m, 1], s=18, alpha=.5, color=COLORS[who], label=who)
    t = data.traps()
    for (x, y), tag in zip(pca.transform(embed(t.text)), t.tag):
        ax.scatter(x, y, s=220, marker="*", color="#f2a900", edgecolor="black", zorder=3)
        ax.annotate(tag, (x, y), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=12,
                    bbox=dict(fc="white", ec="none", alpha=.85))
    ax.legend(frameon=False)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Every line as a dot (384 numbers squashed to 2)")
    plt.show()
