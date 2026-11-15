"""Download The Art of War (Giles 1910, Project Gutenberg #17405) and split it into numbered verses.

Output: data/suntzu.csv with columns text, chapter, verse, source_url.
Keeps verses of 5-40 words. Strips the "Sun Tzu said:" opener so the model can't cheat on the name.
"""
import csv
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

URL = "https://www.gutenberg.org/cache/epub/17405/pg17405.txt"
OUT = Path(__file__).resolve().parent.parent / "data" / "suntzu.csv"
ROMAN = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII)\. [A-Z ]+$")
VERSE = re.compile(r"^(\d+(?:, \d+)*)\. (.*)")


def clean(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()  # Tzŭ -> Tzu, ’ dropped
    s = s.replace("_", "")
    s = re.sub(r"^Sun Tzu said:\s*", "", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    raw = urllib.request.urlopen(URL, timeout=30).read().decode("utf-8")
    # straighten curly quotes before the ascii fold drops them
    raw = raw.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", " - ")
    body = raw.split("*** START OF")[1].split("*** END OF")[0]
    lines = body.splitlines()

    rows, chapter, cur = [], None, None
    for line in lines:
        s = line.strip()
        if ROMAN.match(s):
            chapter = s.split(".")[0]
            continue
        if chapter is None:
            continue
        m = VERSE.match(s)
        if m:
            if cur:
                rows.append(cur)
            cur = {"chapter": chapter, "verse": m.group(1), "text": m.group(2)}
        elif s and cur:
            cur["text"] += " " + s
        elif not s and cur:
            rows.append(cur)
            cur = None
    if cur:
        rows.append(cur)

    kept = []
    for r in rows:
        t = clean(r["text"])
        n = len(t.split())
        if 5 <= n <= 40:
            kept.append({"text": t, "chapter": r["chapter"], "verse": r["verse"], "source_url": URL})

    if len(kept) < 200:
        sys.exit(f"Only {len(kept)} verses parsed - the Gutenberg format probably changed.")
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "chapter", "verse", "source_url"])
        w.writeheader()
        w.writerows(kept)
    print(f"{len(rows)} verses parsed, {len(kept)} kept (5-40 words) -> {OUT}")


if __name__ == "__main__":
    main()
