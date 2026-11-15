"""Step 2 of the evidence: train the review flagger and test it honestly.

    python evaluate_qe.py

Train on FLORES+ "dev". Test on FLORES+ "devtest", which the flagger never sees.
A translation counts as BAD when its chrF score against the professional
translation is in the bottom quarter for its language (the cut-off is set on
dev and then applied unchanged to devtest).

Prints the results and saves:
    data/model.json     the trained flagger, used by the app
    data/results.json   every number shown in the app's Evidence section
"""

from __future__ import annotations

import glob
import json
import os
import random

import numpy as np

from build_dataset import out_dir
from models import TARGETS, use_standin
from qe import Flagger, signals

BUDGETS = [0.1, 0.2, 0.3, 0.4, 0.5]   # share of translations a human is willing to review
BAD_SHARE = 0.25


def load(name: str) -> list[dict]:
    rows = []
    for path in sorted(glob.glob(os.path.join(out_dir(), f"{name}_*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            rows += [json.loads(line) for line in f]
    return rows


def features(rows, typical) -> list[dict]:
    return [signals(r["source"], r["translation"], r["back"], r["language"],
                    confidence=r["confidence"], meaning_similarity=r["similarity"],
                    typical_log_ratio=typical.get(r["language"], typical["*"])) for r in rows]


def auroc(labels, scores) -> float | None:
    """Chance that a random bad translation scores higher than a random good one. 0.5 = guessing."""
    from sklearn.metrics import roc_auc_score
    return None if len(set(labels)) < 2 else float(roc_auc_score(labels, scores))


def caught(labels, scores, languages, budget) -> float:
    """If a human reviews the top `budget` share in each language, what share of bad ones do they see?"""
    labels, scores, languages = np.array(labels), np.array(scores), np.array(languages)
    hit = 0
    for lang in set(languages):
        idx = np.where(languages == lang)[0]
        k = max(1, round(budget * len(idx)))
        top = idx[np.argsort(-scores[idx], kind="stable")[:k]]
        hit += labels[top].sum()
    return float(hit / max(1, labels.sum()))


def main():
    dev, test = load("dev"), load("devtest")
    if not dev or not test:
        raise SystemExit("No data yet. Run build_dataset.py first.")

    # the label: bottom quarter by chrF within each language, cut-off learned on dev
    cut = {lang: float(np.quantile([r["chrf_ref"] for r in dev if r["language"] == lang], BAD_SHARE))
           for lang in TARGETS if any(r["language"] == lang for r in dev)}
    for r in dev + test:
        r["bad"] = int(r["chrf_ref"] < cut[r["language"]])

    typical = Flagger.learn_length_ratios(dev)
    flagger = Flagger()
    flagger.typical_log_ratio = typical
    flagger.fit(features(dev, typical), [r["bad"] for r in dev])

    X_test = features(test, typical)
    y = [r["bad"] for r in test]
    langs = [r["language"] for r in test]
    rng = random.Random(0)
    methods = {
        "LocaleOS flagger": list(flagger.score(X_test)),
        "Translator confidence alone": [x["low_confidence"] for x in X_test],
        "Longest sentences first": [len(r["source"]) for r in test],
        "Random": [rng.random() for _ in test],
    }

    results = {"standin": use_standin(), "train_rows": len(dev), "test_rows": len(test),
               "bad_share": BAD_SHARE, "budgets": BUDGETS, "languages": {}, "overall": {}, "curve": {}}
    for name, s in methods.items():
        results["overall"][name] = {"auroc": auroc(y, s), "caught_at_20": caught(y, s, langs, 0.2)}
        results["curve"][name] = [caught(y, s, langs, b) for b in BUDGETS]
    results["curve"]["Random"] = BUDGETS[:]            # the exact expectation, not one noisy draw
    results["overall"]["Random"] = {"auroc": 0.5, "caught_at_20": 0.2}

    for lang in sorted(set(langs)):
        idx = [i for i, l in enumerate(langs) if l == lang]
        pick = lambda v: [v[i] for i in idx]
        results["languages"][lang] = {
            "n": len(idx),
            "mean_chrf": float(np.mean([test[i]["chrf_ref"] for i in idx])),
            "bad_rate": float(np.mean(pick(y))),
            **{name: {"auroc": auroc(pick(y), pick(s)), "caught_at_20": caught(pick(y), pick(s), pick(langs), 0.2)}
               for name, s in methods.items() if name != "Random"},
        }

    # our own question: does it work on a language it never trained on?
    results["unseen_language"] = {}
    for lang in sorted(set(langs)):
        others = [r for r in dev if r["language"] != lang]
        if len({r["language"] for r in others}) < 2:
            continue
        t = Flagger.learn_length_ratios(others)
        f = Flagger()
        f.typical_log_ratio = t
        f.fit(features(others, t), [r["bad"] for r in others])
        rows = [r for r in test if r["language"] == lang]
        s = list(f.score(features(rows, t)))
        yy = [r["bad"] for r in rows]
        results["unseen_language"][lang] = {"auroc": auroc(yy, s), "caught_at_20": caught(yy, s, [lang] * len(rows), 0.2)}

    # where it fails: bad translations it scored lowest, good ones it scored highest
    scores = methods["LocaleOS flagger"]
    results["failures"] = {}
    for lang in sorted(set(langs)):
        idx = [i for i, l in enumerate(langs) if l == lang]
        show = lambda i: {k: test[i][k] for k in ("source", "translation", "reference", "back")} | {"score": float(scores[i])}
        missed = sorted([i for i in idx if y[i]], key=lambda i: scores[i])[:5]
        false_alarms = sorted([i for i in idx if not y[i]], key=lambda i: -scores[i])[:5]
        results["failures"][lang] = {"missed": [show(i) for i in missed], "false_alarms": [show(i) for i in false_alarms]}

    results["weights"] = dict(zip(flagger.to_json()["features"], flagger.to_json()["coef"]))

    with open(os.path.join(out_dir(), "model.json"), "w", encoding="utf-8") as f:
        json.dump(flagger.to_json(), f, indent=2)
    with open(os.path.join(out_dir(), "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    if use_standin():
        print("STAND-IN MODELS: these numbers are meaningless except as a test of the code.\n")
    print(f"Trained on {len(dev)} dev translations, tested on {len(test)} devtest translations.\n")
    print(f"{'method':30}{'AUROC':>8}{'bad ones caught reviewing 20%':>32}")
    for name, m in results["overall"].items():
        print(f"{name:30}{m['auroc']:>8.2f}{m['caught_at_20']:>31.0%}")
    print(f"\n{'language':12}{'n':>5}{'bad':>7}{'flagger AUROC':>15}{'caught@20%':>12}{'unseen-language AUROC':>24}")
    for lang, m in results["languages"].items():
        u = results["unseen_language"].get(lang, {}).get("auroc")
        fmt = lambda v: "   n/a" if v is None else f"{v:6.2f}"
        print(f"{lang:12}{m['n']:>5}{m['bad_rate']:>7.0%}{fmt(m['LocaleOS flagger']['auroc']):>15}"
              f"{m['LocaleOS flagger']['caught_at_20']:>12.0%}{fmt(u):>24}")
    print(f"\nSaved model.json and results.json in {out_dir()}")


if __name__ == "__main__":
    main()
