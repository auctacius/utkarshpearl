"""Does the bridge actually beat asking directly? Measured per language.

Uses Belebele (Meta), a reading test where the SAME passages and questions
exist in 100+ languages, each with 4 answer choices and one correct answer.
The baseline is asking the model directly in the user's language.

Colab, T4 GPU:  python evaluate.py --n 100
Writes results to data/route_table.json and data/eval_results.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time

from bridge import NLLB_CODES, Bridge, HERE

PROMPT = (
    "Read the passage and answer the question. Reply with only the number "
    "of the correct choice (1, 2, 3 or 4).\n\nPassage: {p}\n\nQuestion: {q}\n\n"
    "1) {a1}\n2) {a2}\n3) {a3}\n4) {a4}"
)


def load_belebele(code: str, n: int):
    from datasets import load_dataset

    # Belebele's config names match the NLLB codes. If one is missing for a
    # language, this raises; report it rather than guessing.
    ds = load_dataset("facebook/belebele", code, split="test")
    return ds.select(range(min(n, len(ds))))


def pick_number(text: str):
    m = re.search(r"[1-4]", text)
    return int(m.group()) if m else None


def ask_direct(b: Bridge, row, language):
    prompt = PROMPT.format(p=row["flores_passage"], q=row["question"], a1=row["mc_answer1"],
                           a2=row["mc_answer2"], a3=row["mc_answer3"], a4=row["mc_answer4"])
    answer, read, wrote = b.chat(prompt, language, max_new_tokens=5)
    return pick_number(answer), read + wrote


def ask_bridged(b: Bridge, row, language):
    t = lambda s: b.translate(s, language, "English")
    prompt = PROMPT.format(p=t(row["flores_passage"]), q=t(row["question"]), a1=t(row["mc_answer1"]),
                           a2=t(row["mc_answer2"]), a3=t(row["mc_answer3"]), a4=t(row["mc_answer4"]))
    answer, read, wrote = b.chat(prompt, "English", max_new_tokens=5)
    return pick_number(answer), read + wrote


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100, help="questions per language")
    ap.add_argument("--languages", nargs="*", default=list(NLLB_CODES))
    args = ap.parse_args()

    b = Bridge()
    results, failures = {}, {}
    for lang in args.languages:
        try:
            rows = load_belebele(NLLB_CODES[lang], args.n)
        except Exception as e:
            print(f"{lang}: Belebele not available ({e}); skipped")
            continue
        start = time.time()
        stats = {"direct": [0, 0], "bridged": [0, 0]}  # [correct, tokens]
        failures[lang] = []
        for row in rows:
            gold = int(row["correct_answer_num"])
            for route, fn in (("direct", ask_direct), ("bridged", ask_bridged)):
                if lang == "English" and route == "bridged":
                    continue
                pred, tokens = fn(b, row, lang)
                stats[route][0] += pred == gold
                stats[route][1] += tokens
                if route == "direct" and pred != gold and len(failures[lang]) < 5:
                    failures[lang].append({"question": row["question"], "gold": gold, "predicted": pred})
        n = len(rows)
        results[lang] = {
            "n": n,
            "direct_accuracy": stats["direct"][0] / n,
            "bridged_accuracy": None if lang == "English" else stats["bridged"][0] / n,
            "direct_tokens_per_question": stats["direct"][1] / n,
            "bridged_tokens_per_question": None if lang == "English" else stats["bridged"][1] / n,
        }
        print(f"{lang:10} direct {results[lang]['direct_accuracy']:.0%}  "
              f"bridged {results[lang]['bridged_accuracy'] if results[lang]['bridged_accuracy'] is None else format(results[lang]['bridged_accuracy'], '.0%')}"
              f"  ({time.time() - start:.0f}s)")

    routes = {"_status": "MEASURED by evaluate.py on Belebele; see eval_results.json for sample size."}
    for lang, r in results.items():
        bridged_better = r["bridged_accuracy"] is not None and r["bridged_accuracy"] > r["direct_accuracy"]
        routes[lang] = {"route": "bridged" if bridged_better else "direct",
                        "direct_accuracy": r["direct_accuracy"], "bridged_accuracy": r["bridged_accuracy"]}
    with open(os.path.join(HERE, "data", "route_table.json"), "w", encoding="utf-8") as f:
        json.dump(routes, f, indent=2, ensure_ascii=False)
    with open(os.path.join(HERE, "data", "eval_results.json"), "w", encoding="utf-8") as f:
        json.dump({"results": results, "example_failures": failures}, f, indent=2, ensure_ascii=False)
    print("\nSaved data/route_table.json and data/eval_results.json")


if __name__ == "__main__":
    main()
