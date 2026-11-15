#!/usr/bin/env python3
"""
translate.py -- run the free NLLB-200 translator on our English sentences (one language per run).

Run it in Google Colab with a GPU (Runtime > Change runtime type > T4 GPU). CPU also works for
60 short sentences, just slower.

    !pip -q install transformers sentencepiece sacrebleu
    !python src/translate.py --lang hi --limit 5      # smoke test first (5 sentences)
    !python src/translate.py --lang hi                # the real run

Writes outputs/translations_<lang>.csv with the columns in CONTRACT.md. For each sentence we also
translate the result BACK to English (the "back-translation"): it is the input of our round-trip
quality-score baseline. Raters must NOT see it.

NOTE: drafted without access to a GPU; if something breaks, read the error, fix it and tell the lead.
"""
import argparse
import csv
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "facebook/nllb-200-distilled-600M"
SYSTEM_NAME = "nllb600m"
# NLLB language codes: English, Hindi (Devanagari), Arabic (Modern Standard), Chinese (Simplified).
NLLB_CODES = {"en": "eng_Latn", "hi": "hin_Deva", "ar": "arb_Arab", "zh": "zho_Hans"}


def translate_texts(model, tokenizer, texts, src_code, tgt_code, device, batch_size=12):
    """Translate a list of sentences from src_code to tgt_code, a few at a time."""
    import torch

    results = []
    tokenizer.src_lang = src_code  # tells the tokenizer which language the input is in
    forced_start = tokenizer.convert_tokens_to_ids(tgt_code)  # makes the model write in the target language
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        enc = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=256).to(device)
        with torch.inference_mode():
            out = model.generate(**enc, forced_bos_token_id=forced_start, num_beams=4, max_new_tokens=200)
        results.extend(tokenizer.batch_decode(out, skip_special_tokens=True))
    return results


def main():
    ap = argparse.ArgumentParser(description="Translate data/sentences_en.csv with NLLB-200.")
    ap.add_argument("--lang", required=True, choices=["hi", "zh", "ar"])
    ap.add_argument("--zh-script", choices=["hans", "hant"], default="hans",
                    help="Chinese only: Simplified (default) or Traditional. Mention your choice in the write-up.")
    ap.add_argument("--limit", type=int, default=0, help="only the first N sentences (smoke test)")
    ap.add_argument("--out", default="", help="output CSV (default outputs/translations_<lang>.csv)")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("device:", device)

    with open(ROOT / "data" / "sentences_en.csv", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device).eval()

    target = NLLB_CODES[args.lang]
    model_label = MODEL_NAME
    if args.lang == "zh" and args.zh_script == "hant":
        target, model_label = "zho_Hant", MODEL_NAME + " [zho_Hant]"

    english = [r["src_en"] for r in rows]
    forward = translate_texts(model, tokenizer, english, NLLB_CODES["en"], target, device)
    back = translate_texts(model, tokenizer, forward, target, NLLB_CODES["en"], device)

    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    out_path = Path(args.out) if args.out else ROOT / "outputs" / f"translations_{args.lang}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sentence_id", "lang", "system", "src_en", "translation", "back_translation", "model_name", "created_utc"])
        for r, fw, bk in zip(rows, forward, back):
            w.writerow([r["sentence_id"], args.lang, SYSTEM_NAME, r["src_en"], fw, bk, model_label, stamp])
    print(f"wrote {len(rows)} rows to {out_path}")
    print(f"next: python tools/tie_out.py --lang {args.lang} --stage translations")


if __name__ == "__main__":
    main()
