import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tvt import TAYLOR, chance_of_taylor, load, quiz, train, traps


def rows(model, df, note_column):
    p = chance_of_taylor(model, list(df.text))
    return [{"text": t, "label": l, "note": n, "p": round(float(x), 3)}
            for t, l, n, x in zip(df.text, df.label, df[note_column], p)]


def main():
    lines = load()
    model, accuracy, _ = train(lines)
    sign = 1 if model.classes_[1] == TAYLOR else -1
    site = {
        "coef": [round(float(x), 5) for x in sign * model.coef_[0]],
        "intercept": round(float(sign * model.intercept_[0]), 5),
        "accuracy": round(float(accuracy), 3),
        "n_test": math.ceil(len(lines) * 0.2),
        "rounds": rows(model, quiz(), "why_its_here"),
        "traps": rows(model, traps(), "note"),
    }
    (ROOT / "docs" / "model.json").write_text(json.dumps(site, separators=(",", ":")))
    print(f"accuracy {accuracy:.3f} on {site['n_test']} lines")


if __name__ == "__main__":
    main()
