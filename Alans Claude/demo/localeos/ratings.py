"""Native-speaker check: does the flagger agree with a real speaker?

    python ratings.py make     # writes one CSV per language for a teammate to fill in
    python ratings.py score    # reads the filled CSVs and reports agreement

Each CSV has 30 translations: 20 from our business strings and 10 from the
FLORES+ test set. It does NOT show the flagger's score, so the rating is blind.
In the "rating" column the speaker types:
    ok     a customer would understand it correctly
    bad    it is wrong, confusing or misleading, and a human should fix it

Run build_dataset.py --business and evaluate_qe.py first.
"""

from __future__ import annotations

import csv
import json
import os
import random
import sys

from build_dataset import out_dir
from evaluate_qe import features, load
from models import TARGETS
from qe import Flagger

N_BUSINESS, N_FLORES = 20, 10


def scored(name: str, flagger: Flagger) -> list[dict]:
    rows = load(name)
    if rows:
        for r, s in zip(rows, flagger.score(features(rows, flagger.typical_log_ratio))):
            r["score"], r["band"] = float(s), flagger.band(float(s))
    return rows


def pick(rows, n, rng):
    """Half from the riskiest, half from the rest, so both kinds get rated."""
    rows = sorted(rows, key=lambda r: -r["score"])
    top = rows[: max(1, len(rows) // 5)]
    rest = rows[len(top):]
    chosen = rng.sample(top, min(n // 2, len(top))) + rng.sample(rest, min(n - n // 2, len(rest)))
    rng.shuffle(chosen)
    return chosen


def make():
    flagger = Flagger.load(os.path.join(out_dir(), "model.json"))
    business, flores = scored("business", flagger), scored("devtest", flagger)
    if not business:
        raise SystemExit("Run `python build_dataset.py --business` first.")
    rng, key = random.Random(7), {}
    for lang in TARGETS:
        rows = pick([r for r in business if r["language"] == lang], N_BUSINESS, rng) + \
               pick([r for r in flores if r["language"] == lang], N_FLORES, rng)
        if not rows:
            continue
        path = os.path.join(out_dir(), f"ratings_{lang}.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig so Excel shows the scripts correctly
            w = csv.writer(f)
            w.writerow(["item", "english", f"translation ({lang})", "rating (ok / bad)", "note (optional)"])
            for i, r in enumerate(rows, 1):
                w.writerow([i, r["source"], r["translation"], "", ""])
                key[f"{lang}:{i}"] = {"set": r["set"], "score": r["score"], "band": r["band"]}
        print(f"wrote {path}")
    with open(os.path.join(out_dir(), "ratings_key.json"), "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2)
    print("\nSend each CSV to the teammate who speaks that language. They fill in the rating column,\n"
          "save it under the same name, and you run:  python ratings.py score")


def score():
    with open(os.path.join(out_dir(), "ratings_key.json"), encoding="utf-8") as f:
        key = json.load(f)
    human = {}
    for lang in TARGETS:
        path = os.path.join(out_dir(), f"ratings_{lang}.csv")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))[1:]
        rated = [(key[f"{lang}:{r[0]}"], r[3].strip().lower()) for r in rows if len(r) > 3 and r[3].strip()]
        rated = [(k, v == "bad") for k, v in rated if v in ("ok", "bad")]
        if not rated:
            print(f"{lang}: no ratings filled in yet")
            continue
        flagged = [k["band"] != "clear" for k, _ in rated]
        bad = [b for _, b in rated]
        tp = sum(f and b for f, b in zip(flagged, bad))
        human[lang] = {
            "rated": len(rated), "human_bad": sum(bad), "flagged": sum(flagged),
            "agreement": sum(f == b for f, b in zip(flagged, bad)) / len(rated),
            "bad_caught": None if not sum(bad) else tp / sum(bad),
            "flags_correct": None if not sum(flagged) else tp / sum(flagged),
        }
        h = human[lang]
        pct = lambda v: "n/a" if v is None else f"{v:.0%}"
        print(f"{lang:10} rated {h['rated']:>2}  speaker said bad: {h['human_bad']:>2}  flagger agreed on {pct(h['agreement'])}"
              f"  caught {pct(h['bad_caught'])} of the bad ones  {pct(h['flags_correct'])} of its flags were right")
    if human:
        path = os.path.join(out_dir(), "results.json")
        with open(path, encoding="utf-8") as f:
            results = json.load(f)
        results["human"] = human
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nAdded the native-speaker results to {path}")


if __name__ == "__main__":
    {"make": make, "score": score}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
