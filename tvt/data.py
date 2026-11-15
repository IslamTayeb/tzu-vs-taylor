import re
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
TAYLOR, SUN_TZU = "Taylor", "Sun Tzu"


def _key(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


def quiz():
    return pd.read_csv(DATA / "quiz.csv")


def traps():
    return pd.read_csv(DATA / "traps.csv")


def load(seed=0, n=300):
    held_out = {_key(t) for t in pd.concat([quiz().text, traps().text])}
    lines = pd.concat([
        pd.read_csv(DATA / "suntzu.csv").assign(label=SUN_TZU),
        pd.read_csv(DATA / "taylor.csv").assign(label=TAYLOR),
    ], ignore_index=True)[["text", "label"]]
    lines = lines[~lines.text.map(_key).isin(held_out)]
    return lines.groupby("label").sample(n, random_state=seed).reset_index(drop=True)
