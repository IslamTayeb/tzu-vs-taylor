from pathlib import Path

import style
from style import NIGHT, plt

style.apply()
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.set_xlim(0, 8); ax.set_ylim(0, 3.2); ax.axis("off")
style.doodle(ax, "Taylor", 1.6, 1.6, 2.6)
style.doodle(ax, "Sun Tzu", 6.4, 1.6, 2.6)
ax.text(4, 1.6, "vs", ha="center", va="center", fontsize=40, color=NIGHT)
ax.set_aspect("equal")
for ext in ("png", "svg"):
    fig.savefig(Path(__file__).parent / f"title.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.2, transparent=True)
