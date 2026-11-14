"""The full Language Tax study on FLORES+ (1,012 professionally translated
sentences per language), replacing the 12-sentence pilot.

FLORES+ needs a free Hugging Face account with the dataset's terms accepted:
https://huggingface.co/datasets/openlanguagedata/flores_plus
In Colab:  from huggingface_hub import login; login()
Then:      python flores_study.py
"""

from __future__ import annotations

import json
import os

from bridge import NLLB_CODES, HERE
from tax import format_table, strip_accents, tax_table
from tokenizers_lib import load_tokenizers


def load_flores(code: str, split: str = "devtest"):
    from datasets import load_dataset

    ds = load_dataset("openlanguagedata/flores_plus", code, split=split)
    return [row["text"] for row in ds]


def main():
    toks = load_tokenizers()
    parallel = {}
    for lang, code in NLLB_CODES.items():
        try:
            parallel[lang] = load_flores(code)
            print(f"{lang}: {len(parallel[lang])} sentences")
        except Exception as e:
            print(f"{lang}: could not load {code} ({e})")
    if "English" not in parallel:
        raise SystemExit("English is required as the baseline.")
    if "Kurmanji" in parallel:
        parallel["Kurmanji (no accents)"] = [strip_accents(s) for s in parallel["Kurmanji"]]
    table = tax_table(toks, parallel)
    print("\nTokens for the same FLORES+ devtest sentences, as a multiple of English:\n")
    print(format_table(table))
    with open(os.path.join(HERE, "data", "flores_tax_results.json"), "w", encoding="utf-8") as f:
        json.dump({m: {l: round(v, 3) for l, v in row.items()} for m, row in table.items()}, f, indent=2)
    print("\nSaved data/flores_tax_results.json")


if __name__ == "__main__":
    main()
