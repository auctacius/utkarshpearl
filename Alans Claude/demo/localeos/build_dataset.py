"""Step 1 of the evidence: translate, back-translate and score the raw material.

For every English sentence and each of our five languages this saves:
    the machine translation      (NLLB-200)
    the translator's confidence
    the back-translation into English
    the meaning similarity       (LaBSE, if available)
    chrF against the professional translation  (FLORES+ only: this becomes the label)

    python build_dataset.py                 # FLORES+ dev and devtest, 400 sentences each
    python build_dataset.py --n 200         # smaller and faster
    python build_dataset.py --business      # our own 60 business strings (no reference)

Each language is saved to its own file as soon as it finishes, so if Colab
disconnects, running the same command again continues where it stopped.
"""

from __future__ import annotations

import argparse
import json
import os

from models import NLLB_CODES, TARGETS, load_models, use_standin
from qe import chrf

HERE = os.path.dirname(os.path.abspath(__file__))

# FLORES+ renamed a few language codes between versions, so we try each spelling.
FLORES_CODES = {
    "English": ["eng_Latn"], "Spanish": ["spa_Latn"], "Hindi": ["hin_Deva"],
    "Mandarin": ["cmn_Hans", "zho_Hans"], "Arabic": ["arb_Arab"], "Kurmanji": ["kmr_Latn"],
}
FLORES_SOURCES = ["openlanguagedata/flores_plus", "facebook/flores"]


def out_dir() -> str:
    d = os.path.join(HERE, "data", "standin") if use_standin() else os.path.join(HERE, "data")
    os.makedirs(d, exist_ok=True)
    return d


def load_flores(language: str, split: str, n: int) -> list[str]:
    """The first n sentences of a FLORES split in one language."""
    from datasets import load_dataset

    errors = []
    for source in FLORES_SOURCES:
        for code in FLORES_CODES[language]:
            try:
                ds = load_dataset(source, code, split=split)
                column = "text" if "text" in ds.column_names else "sentence"
                return [row[column] for row in ds.select(range(min(n, len(ds))))]
            except Exception as e:
                errors.append(f"{source}/{code}: {type(e).__name__}: {str(e)[:90]}")
    raise RuntimeError(
        f"Could not load FLORES for {language}. Log in to Hugging Face and accept the terms at "
        "https://huggingface.co/datasets/openlanguagedata/flores_plus, then try again.\n  " + "\n  ".join(errors))


def load_parallel(split: str, n: int) -> dict[str, list[str]]:
    """English plus the professional translations, sentence-aligned."""
    if use_standin():
        from standin import clean, standin_corpus
        english = standin_corpus(n, seed=1 if split == "dev" else 2)
        return {"English": english, **{lang: [clean(s, lang) for s in english] for lang in TARGETS}}
    return {lang: load_flores(lang, split, n) for lang in NLLB_CODES}


def process(name: str, language: str, english: list[str], references: list[str] | None,
            translator, embedder) -> str:
    """Translate one language and save it. Returns the file path."""
    path = os.path.join(out_dir(), f"{name}_{language}.jsonl")
    if os.path.exists(path) and sum(1 for _ in open(path, encoding="utf-8")) >= len(english):
        print(f"  {name} {language}: already done, skipping")
        return path
    translations, confidences = translator.translate(english, "English", language)
    backs, _ = translator.translate(translations, language, "English")
    similarities = embedder.similarity(english, translations) if embedder else [None] * len(english)
    with open(path, "w", encoding="utf-8") as f:
        for i, source in enumerate(english):
            row = {"id": i, "set": name, "language": language, "source": source,
                   "translation": translations[i], "confidence": confidences[i],
                   "back": backs[i], "similarity": similarities[i]}
            if references is not None:
                row["reference"] = references[i]
                row["chrf_ref"] = chrf(translations[i], references[i])
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  {name} {language}: saved {len(english)} rows")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400, help="sentences per split")
    ap.add_argument("--splits", nargs="*", default=["dev", "devtest"])
    ap.add_argument("--languages", nargs="*", default=TARGETS)
    ap.add_argument("--business", action="store_true", help="translate data/business_strings.json instead")
    args = ap.parse_args()

    translator, embedder, standin = load_models()
    if standin:
        print("STAND-IN MODELS: nothing here is a real translation. Output goes to data/standin/.")

    if args.business:
        with open(os.path.join(HERE, "data", "business_strings.json"), encoding="utf-8") as f:
            english = [s["text"] for s in json.load(f)["strings"]]
        for language in args.languages:
            process("business", language, english, None, translator, embedder)
        return

    for split in args.splits:
        print(f"{split}:")
        parallel = load_parallel(split, args.n)
        for language in args.languages:
            process(split, language, parallel["English"], parallel[language], translator, embedder)


if __name__ == "__main__":
    main()
