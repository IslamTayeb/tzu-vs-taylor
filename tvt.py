"""Helpers for the "Taylor Swift or Sun Tzu?" notebook."""
import json
import re
from html import escape
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import HTML, display
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

DATA = Path(__file__).resolve().parent / "data"
TAYLOR, TZU = "Taylor", "Sun Tzu"
COLORS = {TAYLOR: "#c2185b", TZU: "#37474f"}

plt.rcParams.update({"font.size": 16, "axes.titlesize": 20, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 110})

state = {}


def say(html, size=28):
    display(HTML(f'<div style="font-size:{size}px;line-height:1.35;margin:8px 0">{html}</div>'))


def _key(s):
    return re.sub(r"\W+", " ", s.lower()).strip()


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
    train, test = train_test_split(df, test_size=0.2, stratify=df.label, random_state=seed)

    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(train.text)
    state.update(df=df, train=train, test=test, quiz=quiz, traps=traps, vec=vec,
                 score={"Class": 0, "Model": 0}, played=set())
    say(f"<b>{n}</b> Sun Tzu lines + <b>{n}</b> Taylor lines "
        f"&rarr; <b>{len(train)}</b> to learn from, <b>{len(test)}</b> kept secret for the test.")


def text_to_numbers(text, top=20):
    vec = state["vec"]
    row = vec.transform([text]).tocoo()
    names = vec.get_feature_names_out()
    pairs = sorted(zip(row.data, (names[j] for j in row.col)), reverse=True)[:top]
    say(f"&ldquo;{escape(text)}&rdquo;", 24)
    if not pairs:
        say("None of these words appear in the training data, so this line becomes all zeros.")
        return
    vals, words = zip(*pairs)
    fig, ax = plt.subplots(figsize=(10, 0.45 * len(words) + 1))
    ax.barh(words[::-1], vals[::-1], color="#78909c")
    ax.set_xlabel("TF-IDF weight (rarer word = bigger)")
    ax.set_title(f"{len(row.data)} of {len(names):,} columns are non-zero")
    plt.show()


def train(C=10):
    t, vec = state["train"], state["vec"]
    model = LogisticRegression(C=C, max_iter=1000).fit(vec.transform(t.text), t.label)
    state["model"] = model
    test = state["test"]
    acc = model.score(vec.transform(test.text), test.label)
    say(f"Accuracy on {len(test)} lines it has never seen: <b style='font-size:48px'>{acc:.0%}</b>")


def prob_taylor(text):
    m = state["model"]
    return m.predict_proba(state["vec"].transform([text]))[0, list(m.classes_).index(TAYLOR)]


def _verdict(text):
    p = prob_taylor(text)
    guess = TAYLOR if p >= 0.5 else TZU
    conf = max(p, 1 - p)
    bar = (f'<div style="display:flex;height:34px;border-radius:6px;overflow:hidden;font-size:18px;color:#fff;max-width:720px">'
           f'<div style="width:{p*100:.0f}%;background:{COLORS[TAYLOR]};padding:5px 10px;white-space:nowrap">Taylor {p:.0%}</div>'
           f'<div style="flex:1;background:{COLORS[TZU]};padding:5px 10px;text-align:right;white-space:nowrap">Sun Tzu {1-p:.0%}</div></div>')
    return guess, conf, bar


def quiz(i):
    q = state["quiz"].set_index("round").loc[i]
    say(f"<span style='color:#888'>Round {i}</span><br>&ldquo;{escape(q.text)}&rdquo;", 34)
    vote = input("Class vote - type T (Taylor) or S (Sun Tzu), then Enter: ").strip().upper()[:1]
    truth = q.label
    guess, conf, bar = _verdict(q.text)
    class_guess = {"T": TAYLOR, "S": TZU}.get(vote)
    if i not in state["played"]:
        state["played"].add(i)
        state["score"]["Class"] += class_guess == truth
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


def top_words(n=15):
    vec, m = state["vec"], state["model"]
    names = vec.get_feature_names_out()
    coef = m.coef_[0] if m.classes_[1] == TAYLOR else -m.coef_[0]
    order = np.argsort(coef)
    fig, axes = plt.subplots(1, 2, figsize=(14, 0.42 * n + 1.5))
    for ax, idx, who in [(axes[0], order[:n], TZU), (axes[1], order[-n:][::-1], TAYLOR)]:
        ax.barh(names[idx][::-1], np.abs(coef[idx])[::-1], color=COLORS[who])
        ax.set_title(f"Words that scream {who}")
        ax.set_xlabel("weight")
    plt.tight_layout()
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
    vec, m = state["vec"], state["model"]
    sign = 1 if m.classes_[1] == TAYLOR else -1
    rounds = [{"text": r.text, "label": r.label, "note": r.why_its_here, "p": round(float(prob_taylor(r.text)), 3)}
              for r in state["quiz"].itertuples()]
    trap_rows = [{"text": r.text, "label": r.label, "note": r.note, "p": round(float(prob_taylor(r.text)), 3)}
                 for r in state["traps"].itertuples()]
    names = vec.get_feature_names_out()
    coef = sign * m.coef_[0]
    order = np.argsort(coef)
    out = {
        "vocab": {w: [round(float(vec.idf_[j]), 4), round(float(coef[j]), 4)] for w, j in vec.vocabulary_.items()},
        "intercept": round(float(sign * m.intercept_[0]), 4),
        "accuracy": round(float(m.score(vec.transform(state["test"].text), state["test"].label)), 3),
        "n_train": len(state["train"]), "n_test": len(state["test"]),
        "top": {"Sun Tzu": [[names[j], round(float(-coef[j]), 3)] for j in order[:15]],
                "Taylor": [[names[j], round(float(coef[j]), 3)] for j in order[-15:][::-1]]},
        "rounds": rounds, "traps": trap_rows,
    }
    Path(path).write_text(json.dumps(out, separators=(",", ":")))
    return out
