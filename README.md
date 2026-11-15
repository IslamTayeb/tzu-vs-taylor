# Taylor Swift or Sun Tzu?

A 30-minute class demo for journalism students: a sentence-embedding model (MiniLM) plus logistic regression that tries to tell *reputation*-era Taylor Swift from Sun Tzu's *The Art of War*.

- **Game:** https://islamtayeb.github.io/tzu-vs-taylor/ (short link: tinyurl.com/tzuvt; runs in the browser, phones included)
- **Slides:** `slides/tzu_vs_taylor_lecture.pptx` (PowerPoint or Google Slides, uses Lato)
- **Notebook:** `tzu_vs_taylor.ipynb`, a short walkthrough of the code

## Run the notebook

1. Open it in Colab: https://colab.research.google.com/github/IslamTayeb/tzu-vs-taylor/blob/main/tzu_vs_taylor.ipynb
2. Runtime → Run all (about a minute on CPU).
3. Play `show.quiz(model, 1)` to `show.quiz(model, 10)` with the class.
4. Show `show.top_words`, `show.vector_map`, then `show.traps`.
5. End with `show.predict(model, "...")` on lines the class makes up.

## Layout

```
tvt/               Python package used everywhere
  data.py          load lines, hold out quiz and trap lines
  model.py         embed, train, score
  show.py          notebook visuals
scripts/
  build_suntzu.py  Gutenberg #17405 -> data/suntzu.csv
  build_taylor.py  verified quotes + Genius lyrics -> data/taylor.csv
  export_site.py   trained weights -> docs/model.json
  build_notebook.py
docs/              GitHub Pages site, no build step
  js/main.js       routing and events
  js/play.js       the quiz
  js/fool.js       live "Fool it" box
  js/model.js      MiniLM in the browser
  js/sketch.js     hand-drawn boxes, bars, doodles (rough.js)
slides/
  build.py         builds the deck from figures/out
  figures/         diagram.py (flat-icon diagram), charts.py, assets/
  tools/           slide helpers and chart style (Carlito font)
data/              CSVs: suntzu, taylor, taylor_quotes, quiz, traps
```

## Rebuild

```bash
pip install -r requirements.txt
python scripts/build_suntzu.py
GENIUS_TOKEN=... python scripts/build_taylor.py
python scripts/export_site.py
python scripts/build_notebook.py
python slides/figures/diagram.py && python slides/figures/charts.py && python slides/build.py
```

## Sources

Sun Tzu: Lionel Giles translation (1910), Project Gutenberg #17405. Taylor Swift: interview quotes checked word for word against TIME (2023) and Vogue (2019); lyrics via the Genius API. Photos (Wikimedia Commons): Taylor Swift by Glenn Francis (CC BY-SA 4.0); Sun Tzu statue by 663highland (CC BY 2.5); Sun Tzu portrait, public domain. Fonts: Virgil (site) and Carlito (slides), SIL Open Font License.
