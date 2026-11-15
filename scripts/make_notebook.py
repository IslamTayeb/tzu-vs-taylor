import nbformat as nbf
C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s, hide=True):
    c = nbf.v4.new_code_cell(s)
    if hide: c.metadata["cellView"] = "form"
    C.append(c)

md("# Taylor Swift or Sun Tzu?\n### Can a computer tell a pop star from a 2,500-year-old general?")
md("**Setup:** run this once. It downloads the data and an AI model that turns sentences into numbers.")
code('''#@title Setup (click ▶)
import os, sys
if "google.colab" in sys.modules and not os.path.exists("tvt.py"):
    !git clone -q https://github.com/IslamTayeb/tzu-vs-taylor
    %cd tzu-vs-taylor
    !pip -q install sentence-transformers
import tvt
tvt.load()''')
md("## 1. Text → numbers\nA pre-trained AI reads each line and squeezes its **meaning** into 384 numbers, called an **embedding**.")
code('''#@title
tvt.text_to_numbers("Trash takes itself out every single time.")''')
md("Lines that mean similar things get similar numbers, even if they share no words.")
code('''#@title
tvt.closest("Trash takes itself out every single time.")''')
md("## 2. Train\nThe model learns which patterns in those numbers mean Taylor and which mean Sun Tzu, then we test it on lines it has **never seen**.")
code('''#@title
tvt.train()''')
md("## 3. Quiz: class vs. model\nI show a line, you vote, then we see who was right.")
for i in range(1, 11):
    code(f"tvt.quiz({i})", hide=False)
md("## 4. What did it learn?\nWe feed it single words, one at a time, and see which ones it's most sure about.")
code('''#@title
tvt.top_words(15)''')
md("And here is every line as a dot. The ★ stars are our trap lines.")
code('''#@title
tvt.vector_map()''')
md("**Notice:** it learned *topics*: war words go to Sun Tzu, love words go to Taylor. So a line about war in Taylor's voice can fool it, and so can Sun Tzu in Gen Z slang.")
md("## 5. Try to fool it\nOur traps first, then your lines.")
code('''#@title
tvt.traps()''')
code('tvt.predict("type your line here")', hide=False)

nb = nbf.v4.new_notebook()
nb.cells = C
nb.metadata["colab"] = {"provenance": []}
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3"}
nbf.write(nb, "tzu_vs_taylor.ipynb")
