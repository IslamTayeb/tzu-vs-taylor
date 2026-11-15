import re
from collections import Counter

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from .data import TAYLOR

EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"
_encoder = None


def embed(texts):
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        _encoder = SentenceTransformer(EMBEDDER)
    return _encoder.encode(list(texts), normalize_embeddings=True, batch_size=64)


def split(vectors, labels, seed=0):
    return train_test_split(vectors, labels, test_size=0.2, stratify=labels, random_state=seed)


def train(lines, seed=0):
    vectors = embed(lines.text)
    x_train, x_test, y_train, y_test = split(vectors, lines.label, seed)
    model = LogisticRegression(max_iter=2000).fit(x_train, y_train)
    return model, model.score(x_test, y_test), vectors


def chance_of_taylor(model, texts):
    single = isinstance(texts, str)
    p = model.predict_proba(embed([texts] if single else texts))[:, list(model.classes_).index(TAYLOR)]
    return float(p[0]) if single else p


def word_scores(model, texts, min_count=2):
    counts = Counter(w for t in texts for w in re.findall(r"[a-z]{3,}", t.lower()))
    words = sorted(w for w, c in counts.items() if c >= min_count)
    return pd.Series(chance_of_taylor(model, words), index=words).sort_values()
