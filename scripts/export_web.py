import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tvt

tvt.load()
tvt.train()
out = tvt.export_web(ROOT / "docs" / "model.json")
print(f"accuracy {out['accuracy']}")
print("Taylor words:", [w for w, _ in out["top"]["Taylor"]])
print("Sun Tzu words:", [w for w, _ in out["top"]["Sun Tzu"]])
for r in out["rounds"] + out["traps"]:
    print(f"{r['p']:.2f}  {r['label']:<22} {r['text'][:60]}")
