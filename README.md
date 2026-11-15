# Taylor Swift or Sun Tzu?

A 30-minute class demo for journalism students: a sentence-embedding model (MiniLM) plus logistic regression that tries to tell *reputation*-era Taylor Swift from Sun Tzu's *The Art of War*.

- **Game for the class:** https://islamtayeb.github.io/tzu-vs-taylor/ (runs fully in the browser, phones included)
- **Slides:** `slides/tzu_vs_taylor_lecture.pptx` (opens in PowerPoint or imports into Google Slides; uses Lato)
- **Notebook:** `tzu_vs_taylor.ipynb`

## Run the notebook

1. Open in Colab: https://colab.research.google.com/github/IslamTayeb/tzu-vs-taylor/blob/main/tzu_vs_taylor.ipynb
2. Runtime → Run all (about 1 minute, CPU is fine).
3. Run `tvt.quiz(1)` … `tvt.quiz(10)` one at a time with the class.
4. Show `tvt.top_words()` and `tvt.vector_map()`, then `tvt.traps()`.
5. End with `tvt.predict("...")` on lines the class makes up.

## Data

| File | What |
|---|---|
| `data/suntzu.csv` | 327 verses (5–40 words), Project Gutenberg #17405, Lionel Giles 1910 translation |
| `data/taylor_quotes.csv` | 19 interview quotes, each checked word for word against TIME (2023) or Vogue (2019) |
| `data/taylor.csv` | Quotes plus 1–2 line lyric chunks from *reputation*, "Bad Blood", "Mean", "Vigilante Shit" (Genius API) |
| `data/quiz.csv` | 10 quiz lines, held out of training |
| `data/traps.csv` | 4 trap lines, held out of training |

## Rebuild

```bash
pip install -r requirements.txt
python scripts/build_suntzu.py
GENIUS_TOKEN=... python scripts/build_taylor.py
python scripts/export_web.py          # site model -> docs/model.json
python slides/figures/make_figures.py # slide figures
```

## Layout

```
docs/            GitHub Pages site (no build step)
  index.html     markup
  style.css      styles
  js/main.js     wiring and routing
  js/play.js     the quiz
  js/fool.js     "Fool it" live input
  js/model.js    loads MiniLM in the browser and scores text
  js/sketch.js   hand-drawn boxes, bars, doodles (rough.js)
tvt.py           notebook helpers
scripts/         data builders and exports
slides/          deck, build script, figure scripts
```
