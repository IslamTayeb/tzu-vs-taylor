"""Apply the slide chart style: make-plots colors, grid and Carlito, which matches the deck's Calibri."""
import glob
import os

import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))


def apply():
    for path in glob.glob(os.path.join(HERE, "fonts", "*.ttf")):
        font_manager.fontManager.addfont(path)
    plt.style.use(os.path.join(HERE, "plot_style.mplstyle"))
