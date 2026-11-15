"""Build data/taylor.csv (text, source_url, kind) from
  (a) data/taylor_quotes.csv - interview quotes, each hand-verified against its source URL
  (b) song lyrics fetched live from the Genius API (reputation + Bad Blood, Mean, Vigilante Shit),
      split into 1-2 line chunks.

Needs env var GENIUS_TOKEN (https://genius.com/api-clients -> "Generate Access Token").
Lyrics are fetched at build time and NOT committed to the public repo (copyright).
"""
import csv
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUOTES = ROOT / "data" / "taylor_quotes.csv"
OUT = ROOT / "data" / "taylor.csv"

EXTRA_SONGS = ["Bad Blood", "Mean", "Vigilante Shit"]


def die(msg):
    sys.stderr.write("\n" + "=" * 70 + f"\nERROR: {msg}\n" + "=" * 70 + "\n")
    sys.exit(1)


def clean_lyrics(raw: str) -> list[list[str]]:
    """Return Taylor's own lyrics as a list of sections, each a list of lines.

    Drops: Genius header junk, parenthetical ad-libs, and sections sung by featured
    artists (e.g. "[Verse 1: Future]" in End Game).
    """
    if "Lyrics" in raw[:400]:
        raw = raw.split("Lyrics", 1)[1]
    raw = re.sub(r"\d*Embed$", "", raw.strip())
    raw = raw.replace("You might also like", "\n")
    raw = re.sub(r"\([^)\[\]]*\)", "", raw)  # ad-libs, even when they span lines
    for a, b in {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', "\u2005": " ", "\u205f": " "}.items():
        raw = raw.replace(a, b)
    sections, cur, skip = [], [], False
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            if cur and not skip:
                sections.append(cur)
            cur = []
            # "[Verse 1: Future]" -> skip unless Taylor is credited on that section
            skip = ":" in s and "taylor" not in s.lower()
            continue
        if not s:
            if cur and not skip:
                sections.append(cur)
            cur = []
            continue
        if not skip:
            cur.append(s)
    if cur and not skip:
        sections.append(cur)
    return sections


def chunk(sections, seen_lines):
    """Drop lines already used anywhere (choruses), then pair consecutive lines within a section."""
    out = []
    for sec in sections:
        fresh = []
        for line in sec:
            k = re.sub(r"\W+", " ", line.lower()).strip()
            if k and k not in seen_lines:
                seen_lines.add(k)
                fresh.append(line)
        for i in range(0, len(fresh), 2):
            out.append(" / ".join(fresh[i:i + 2]))
    return out


def main():
    token = os.environ.get("GENIUS_TOKEN", "").strip()
    if not token:
        die("GENIUS_TOKEN is not set.\n"
            "Get one at https://genius.com/api-clients, then:\n"
            "    export GENIUS_TOKEN=your_token_here\n"
            "In Colab: add it under the key icon (Secrets) as GENIUS_TOKEN.")
    if not QUOTES.exists():
        die(f"{QUOTES} missing - it holds the verified interview quotes.")

    import lyricsgenius
    g = lyricsgenius.Genius(token, timeout=20, retries=3, verbose=False, remove_section_headers=False,
                            skip_non_songs=True)

    songs = []  # (title, url, lyrics)
    album = g.search_album("reputation", "Taylor Swift")
    if album is None:
        die("Genius could not find the album 'reputation'. Token invalid or API down?")
    for t in album.tracks:
        s = t[1] if isinstance(t, tuple) else t.song  # lyricsgenius versions differ
        if not s.lyrics:
            s = g.search_song(s.title, "Taylor Swift")
        if "prologue" in s.title.lower():  # a prose essay, not a song
            continue
        songs.append((s.title, s.url, s.lyrics))
    for title in EXTRA_SONGS:
        s = g.search_song(title, "Taylor Swift")
        if s is None or not s.lyrics:
            die(f"Genius returned no lyrics for '{title}'.")
        songs.append((s.title, s.url, s.lyrics))
        time.sleep(0.5)

    rows, seen, seen_lines = [], set(), set()
    with QUOTES.open() as f:
        for r in csv.DictReader(f):
            rows.append({"text": r["text"], "source_url": r["source_url"], "kind": "interview"})
            seen.add(r["text"].lower())

    for title, url, lyr in songs:
        n = 0
        for c in chunk(clean_lyrics(lyr or ""), seen_lines):
            key = re.sub(r"\W+", " ", c.lower()).strip()
            if not 3 <= len(key.split()) <= 40 or key in seen:
                continue
            seen.add(key)
            rows.append({"text": c, "source_url": url, "kind": "lyric"})
            n += 1
        print(f"  {title:<40} {n:>3} chunks")
        if n == 0:
            die(f"No lyric chunks parsed for '{title}' - Genius page format may have changed.")

    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "source_url", "kind"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} Taylor rows -> {OUT}")


if __name__ == "__main__":
    main()
