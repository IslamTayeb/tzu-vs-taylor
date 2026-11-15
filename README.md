# Taylor Swift or Sun Tzu?

A 30-minute class demo: a sentence-embedding classifier (MiniLM + logistic regression) that tries to tell *reputation*-era Taylor Swift from *The Art of War*.

**Play the game:** https://islamtayeb.github.io/tzu-vs-taylor/

## Run the notebook

1. Open `tzu_vs_taylor.ipynb` in Colab: https://colab.research.google.com/github/IslamTayeb/tzu-vs-taylor/blob/main/tzu_vs_taylor.ipynb
2. If `data/taylor.csv` isn't in the repo, add your Genius token under 🔑 Secrets as `GENIUS_TOKEN` (get one at genius.com/api-clients).
3. Runtime → Run all. Setup takes about 1 minute; training takes a few seconds on CPU.
4. Scroll to section 3 and run `tvt.quiz(1)` … `tvt.quiz(10)` one at a time with the class.
5. End with `tvt.predict("...")` on lines the class makes up.

## Data

| File | What |
|---|---|
| `data/suntzu.csv` | 327 verses (5–40 words) from Project Gutenberg #17405, Lionel Giles 1910 translation |
| `data/taylor_quotes.csv` | 19 interview quotes, each checked word-for-word against TIME (2023) or Vogue (2019) |
| `data/taylor.csv` | Quotes + 1–2 line lyric chunks from *reputation*, "Bad Blood", "Mean", "Vigilante Shit" (built by `scripts/build_taylor.py` from the Genius API) |
| `data/quiz.csv` | 10 quiz lines, held out of training |
| `data/traps.csv` | 4 trap lines, held out of training |

Rebuild everything locally:

```bash
pip install -r requirements.txt
python scripts/build_suntzu.py
GENIUS_TOKEN=... python scripts/build_taylor.py
python scripts/export_web.py
```

The site in `docs/` runs the same model in the browser with transformers.js.
