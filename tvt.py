"""Helpers for the "Taylor Swift or Sun Tzu?" notebook."""
import json
import re
from collections import Counter
from html import escape
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import HTML, display
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

DATA = Path(__file__).resolve().parent / "data"
TAYLOR, TZU = "Taylor", "Sun Tzu"
COLORS = {TAYLOR: "#BE616A", TZU: "#5E9594"}
EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"

plt.rcParams.update({"font.size": 16, "axes.titlesize": 20, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 110})

state = {}


def say(html, size=28):
    display(HTML(f'<div style="font-size:{size}px;line-height:1.35;margin:8px 0">{html}</div>'))


def _key(s):
    return re.sub(r"\W+", " ", s.lower()).strip()


def embed(texts):
    if "st" not in state:
        from sentence_transformers import SentenceTransformer
        state["st"] = SentenceTransformer(EMBEDDER)
    return state["st"].encode(list(texts), normalize_embeddings=True, batch_size=64)


def load(seed=0):
    tzu = pd.read_csv(DATA / "suntzu.csv").assign(label=TZU)
    tay = pd.read_csv(DATA / "taylor.csv").assign(label=TAYLOR)
    quiz = pd.read_csv(DATA / "quiz.csv")
    traps = pd.read_csv(DATA / "traps.csv")
    held = {_key(t) for t in pd.concat([quiz.text, traps.text])}

    df = pd.concat([tzu[["text", "label"]], tay[["text", "label"]]], ignore_index=True)
    df = df[~df.text.map(_key).isin(held)]
    n = df.label.value_counts().min()
    df = df.groupby("label").sample(n, random_state=seed).reset_index(drop=True)
    df["vec"] = list(embed(df.text))
    train, test = train_test_split(df, test_size=0.2, stratify=df.label, random_state=seed)
    state.update(df=df, train=train, test=test, quiz=quiz, traps=traps,
                 score={"Class": 0, "Model": 0}, played=set())
    say(f"<b>{n}</b> Sun Tzu lines + <b>{n}</b> Taylor lines, each turned into <b>384</b> numbers "
        f"&rarr; <b>{len(train)}</b> to learn from, <b>{len(test)}</b> kept secret for the test.")


def text_to_numbers(text):
    v = embed([text])[0]
    say(f"&ldquo;{escape(text)}&rdquo; &rarr; {len(v)} numbers", 24)
    fig, ax = plt.subplots(figsize=(14, 1.6))
    ax.imshow(v[None, :], aspect="auto", cmap="BrBG", vmin=-.15, vmax=.15)
    ax.set_yticks([])
    ax.set_xlabel("each stripe is one number (green = positive, brown = negative)")
    plt.show()
    say("First 8: " + ", ".join(f"{x:+.2f}" for x in v[:8]) + " &hellip;", 20)


def closest(text, k=3):
    df = state["df"]
    sims = np.vstack(df.vec) @ embed([text])[0]
    say(f"Lines whose numbers are closest to &ldquo;{escape(text)}&rdquo;:", 22)
    for j in np.argsort(-sims)[:k]:
        r = df.iloc[j]
        say(f"<span style='color:{COLORS[r.label]}'>{r.label}</span> &nbsp;{sims[j]:.2f} &nbsp;"
            f"&ldquo;{escape(r.text)}&rdquo;", 20)


def train(C=1):
    t, test = state["train"], state["test"]
    m = LogisticRegression(C=C, max_iter=2000).fit(np.vstack(t.vec), t.label)
    state["model"] = m
    acc = m.score(np.vstack(test.vec), test.label)
    state["accuracy"] = acc
    say(f"Accuracy on {len(test)} lines it has never seen: <b style='font-size:48px'>{acc:.0%}</b>")


def prob_taylor(texts):
    m = state["model"]
    single = isinstance(texts, str)
    p = m.predict_proba(embed([texts] if single else texts))[:, list(m.classes_).index(TAYLOR)]
    return float(p[0]) if single else p


def _verdict(text):
    p = prob_taylor(text)
    guess = TAYLOR if p >= 0.5 else TZU
    bar = (f'<div style="display:flex;height:34px;border-radius:6px;overflow:hidden;font-size:18px;color:#fff;max-width:720px">'
           f'<div style="width:{p*100:.0f}%;background:{COLORS[TAYLOR]};padding:5px 10px;white-space:nowrap">Taylor {p:.0%}</div>'
           f'<div style="flex:1;background:{COLORS[TZU]};padding:5px 10px;text-align:right;white-space:nowrap">Sun Tzu {1-p:.0%}</div></div>')
    return guess, max(p, 1 - p), bar


def quiz(i):
    q = state["quiz"].set_index("round").loc[i]
    say(f"<span style='color:#888'>Round {i}</span><br>&ldquo;{escape(q.text)}&rdquo;", 34)
    vote = input("Class vote - type T (Taylor) or S (Sun Tzu), then Enter: ").strip().upper()[:1]
    truth = q.label
    guess, conf, bar = _verdict(q.text)
    if i not in state["played"]:
        state["played"].add(i)
        state["score"]["Class"] += {"T": TAYLOR, "S": TZU}.get(vote) == truth
        state["score"]["Model"] += guess == truth
    say(f"Answer: <b style='color:{COLORS[truth]}'>{truth}</b>", 34)
    say(f"Model says <b>{guess}</b> ({conf:.0%} sure) {'&#10004;' if guess == truth else '&#10008;'}", 26)
    display(HTML(bar))
    scoreboard()


def scoreboard():
    s = state["score"]
    say(f"<div style='margin-top:14px;padding:10px 18px;border:2px solid #ddd;border-radius:10px;display:inline-block'>"
        f"Class <b>{s['Class']}</b> &nbsp;&mdash;&nbsp; Model <b>{s['Model']}</b>"
        f" <span style='color:#999;font-size:18px'>after {len(state['played'])} rounds</span></div>", 30)


def word_scores(min_count=2):
    if "words" not in state:
        counts = Counter(w for t in state["train"].text for w in re.findall(r"[a-z]{3,}", t.lower()))
        words = sorted(w for w, c in counts.items() if c >= min_count)
        state["words"] = pd.Series(prob_taylor(words), index=words)
    return state["words"]


def top_words(n=15):
    s = word_scores().sort_values()
    fig, axes = plt.subplots(1, 2, figsize=(14, 0.42 * n + 1.5))
    for ax, part, who in [(axes[0], s.head(n), TZU), (axes[1], s.tail(n)[::-1], TAYLOR)]:
        vals = part.values if who == TAYLOR else 1 - part.values
        ax.barh(part.index[::-1], vals[::-1], color=COLORS[who])
        ax.set_xlim(0.5, 1)
        ax.set_title(f"Single words that scream {who}")
        ax.set_xlabel(f"chance of {who}")
    plt.tight_layout()
    plt.show()


def vector_map():
    df = state["df"]
    pca = PCA(2, random_state=0).fit(np.vstack(df.vec))
    xy = pca.transform(np.vstack(df.vec))
    fig, ax = plt.subplots(figsize=(11, 8))
    for who in (TZU, TAYLOR):
        m = (df.label == who).values
        ax.scatter(xy[m, 0], xy[m, 1], s=18, alpha=.45, color=COLORS[who], label=who)
    pts = pca.transform(embed(state["traps"].text))
    for (x, y), tag, dy in zip(pts, state["traps"].tag, [14, -22, 14, -22]):
        ax.scatter(x, y, s=220, marker="*", color="#f2a900", edgecolor="black", zorder=3)
        ax.annotate(tag, (x, y), fontsize=13, xytext=(0, dy), textcoords="offset points", ha="center",
                    bbox=dict(boxstyle="round,pad=.2", fc="white", ec="none", alpha=.85), zorder=4)
    ax.legend(frameon=False)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Every line as a dot (384 numbers squashed to 2)")
    plt.show()


def predict(text):
    guess, conf, bar = _verdict(text)
    say(f"&ldquo;{escape(text)}&rdquo;", 26)
    say(f"&rarr; <b style='color:{COLORS[guess]}'>{guess}</b> ({conf:.0%} sure)", 26)
    display(HTML(bar))


def traps():
    for _, t in state["traps"].iterrows():
        predict(t.text)
        say(f"<span style='color:#888'>Really: <b>{t.label}</b> &mdash; {escape(t.note)}</span>", 18)
        display(HTML("<hr style='opacity:.3'>"))


def export_web(path):
    m = state["model"]
    sign = 1 if m.classes_[1] == TAYLOR else -1
    row = lambda text, label, note: {"text": text, "label": label, "note": note, "p": round(prob_taylor(text), 3)}
    s = word_scores().sort_values()
    out = {
        "model": EMBEDDER,
        "coef": [round(float(x), 5) for x in sign * m.coef_[0]],
        "intercept": round(float(sign * m.intercept_[0]), 5),
        "accuracy": round(float(state["accuracy"]), 3),
        "n_train": len(state["train"]), "n_test": len(state["test"]),
        "top": {"Sun Tzu": [[w, round(1 - float(p), 3)] for w, p in s.head(15).items()],
                "Taylor": [[w, round(float(p), 3)] for w, p in s.tail(15)[::-1].items()]},
        "rounds": [row(r.text, r.label, r.why_its_here) for r in state["quiz"].itertuples()],
        "traps": [row(r.text, r.label, r.note) for r in state["traps"].itertuples()],
    }
    Path(path).write_text(json.dumps(out, separators=(",", ":")))
    return out
