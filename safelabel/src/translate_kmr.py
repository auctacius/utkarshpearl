#!/usr/bin/env python3
"""
translate_kmr.py -- the same translation run as translate.py, for Kurmanji (Northern Kurdish, Latin script).

Kurmanji is an EXTRA, exploratory language added by Person A. It is not one of the three main
languages in CONTRACT.md, so its rows are kept in their own file and are never mixed into the main
results unless the lead decides to add it.

    python src/translate_kmr.py --limit 5    # smoke test
    python src/translate_kmr.py              # all 60 sentences

Writes outputs/translations_kmr.csv with the same columns as the other languages. It reuses
translate_texts() from translate.py, so the model, beam size and settings are identical.
"""
import argparse
import csv
import datetime
from pathlib import Path

from translate import MODEL_NAME, SYSTEM_NAME, translate_texts  # same model and settings as the main run

ROOT = Path(__file__).resolve().parents[1]
ENGLISH, KURMANJI = "eng_Latn", "kmr_Latn"   # NLLB language codes


def main():
    ap = argparse.ArgumentParser(description="Translate data/sentences_en.csv into Kurmanji with NLLB-200.")
    ap.add_argument("--limit", type=int, default=0, help="only the first N sentences (smoke test)")
    ap.add_argument("--out", default="", help="output CSV (default outputs/translations_kmr.csv)")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    with open(ROOT / "data" / "sentences_en.csv", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device).eval()

    english = [r["src_en"] for r in rows]
    forward = translate_texts(model, tokenizer, english, ENGLISH, KURMANJI, device)   # English -> Kurmanji
    back = translate_texts(model, tokenizer, forward, KURMANJI, ENGLISH, device)      # and back, for the round-trip score

    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    out_path = Path(args.out) if args.out else ROOT / "outputs" / "translations_kmr.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sentence_id", "lang", "system", "src_en", "translation", "back_translation", "model_name", "created_utc"])
        for r, fw, bk in zip(rows, forward, back):
            w.writerow([r["sentence_id"], "kmr", SYSTEM_NAME, r["src_en"], fw, bk, MODEL_NAME, stamp])
    print(f"wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
