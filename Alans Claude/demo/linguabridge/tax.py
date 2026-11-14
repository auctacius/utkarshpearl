"""The Language Tax: how many more tokens the same meaning costs per language.

Run directly to print the table:  python tax.py
"""

from __future__ import annotations

import json
import os
import unicodedata
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
LANGUAGES = ["English", "Spanish", "Hindi", "Mandarin", "Arabic", "Kurmanji"]


def load_pilot() -> Dict[str, List[str]]:
    with open(os.path.join(HERE, "data", "pilot_sentences.json"), encoding="utf-8") as f:
        d = json.load(f)
    return {k: v for k, v in d.items() if not k.startswith("_")}


def strip_accents(text: str) -> str:
    """Remove accent marks the way people often type (ê -> e, ş -> s)."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def tax_table(toks, parallel: Dict[str, List[str]]) -> Dict[str, Dict[str, float]]:
    """For each tokenizer and language: total tokens / English total tokens."""
    table = {}
    for name, tok in toks.items():
        en = sum(tok.count(s) for s in parallel["English"])
        table[name] = {lang: sum(tok.count(s) for s in sents) / en for lang, sents in parallel.items()}
    return table


def format_table(table) -> str:
    langs = list(next(iter(table.values())).keys())
    lines = [f"{'tokenizer':16}" + "".join(f"{l[:10]:>11}" for l in langs)]
    for name, row in table.items():
        lines.append(f"{name:16}" + "".join(f"{row[l]:>10.2f}x" for l in langs))
    return "\n".join(lines)


if __name__ == "__main__":
    from tokenizers_lib import load_tokenizers

    toks = load_tokenizers()
    pilot = load_pilot()
    pilot["Kurmanji (no accents)"] = [strip_accents(s) for s in pilot["Kurmanji"]]
    print("\nTokens needed for the same 12 sentences, as a multiple of English:\n")
    print(format_table(tax_table(toks, pilot)))
