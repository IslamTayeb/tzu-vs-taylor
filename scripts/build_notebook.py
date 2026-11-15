from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent

SETUP = '''#@title Setup: run once
import os, sys
if "google.colab" in sys.modules and not os.path.exists("tvt"):
    !git clone -q https://github.com/IslamTayeb/tzu-vs-taylor
    %cd tzu-vs-taylor
    !pip -q install sentence-transformers'''

CELLS = [
    ("md", "# Taylor Swift or Sun Tzu?\nCan a computer tell a pop star from a 2,500-year-old general?"),
    ("code", SETUP),

    ("md", "## 1. The data\nEvery row is one line and who said it."),
    ("code", '''from tvt import load, embed, chance_of_taylor, show

lines = load()          # equal numbers of Sun Tzu and Taylor lines
lines.sample(5)'''),

    ("md", "## 2. Text to numbers\nA pre-trained AI model reads each line and turns its meaning into 384 numbers, called an *embedding*."),
    ("code", '''vectors = embed(lines.text)   # one row of 384 numbers per line
vectors.shape'''),
    ("code", 'show.stripe("Trash takes itself out every single time.")'),
    ("md", "Lines that mean similar things get similar numbers, even with no words in common."),
    ("code", 'show.closest(lines, vectors, "My ex is spreading rumors about me")'),

    ("md", "## 3. Train, then test\nHide 20% of the lines, learn from the rest, then check the hidden ones."),
    ("code", '''from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

x_train, x_test, y_train, y_test = train_test_split(
    vectors, lines.label, test_size=0.2, stratify=lines.label, random_state=0)

model = LogisticRegression(max_iter=2000).fit(x_train, y_train)   # learn which patterns mean Taylor
show.accuracy(model.score(x_test, y_test), len(y_test))           # grade it on lines it never saw'''),

    ("md", "## 4. Class vs. model\nRead the line, vote, then see who was right."),
    *[("code", f"show.quiz(model, {i})") for i in range(1, 8)],

    ("md", "## 5. What did it learn?\nFeed it single words and see which ones it is most sure about."),
    ("code", "show.top_words(model, lines)"),
    ("md", "Every line as a dot. Stars are our trap lines."),
    ("code", "show.vector_map(lines, vectors)"),

    ("md", "## 6. Fool it\nSmall edits to real Sun Tzu verses, and a real Taylor line about enemies."),
    ("code", "show.traps(model)"),
    ("code", 'show.predict(model, "type your own line here")'),
]


def main():
    nb = nbf.v4.new_notebook()
    for kind, source in CELLS:
        cell = nbf.v4.new_markdown_cell(source) if kind == "md" else nbf.v4.new_code_cell(source)
        if source.startswith("#@title"):
            cell.metadata["cellView"] = "form"
        nb.cells.append(cell)
    nb.metadata["colab"] = {"provenance": []}
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3"}
    nbf.write(nb, ROOT / "tzu_vs_taylor.ipynb")


if __name__ == "__main__":
    main()
