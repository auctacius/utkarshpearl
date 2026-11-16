#!/usr/bin/env python3
"""
make_rating_sheet.py -- make the BLIND rating sheet for one language (standard library only).

    python tools/make_rating_sheet.py --lang hi        # reads outputs/translations_hi.csv, writes outputs/RATE_ME_hi.csv

The sheet holds the English and the machine translation plus EMPTY rating columns. It deliberately leaves out the
back-translation so the rater stays blind (see data/RATING_GUIDE.md).

How to rate it:
  * fastest: open tools/rate.html in a browser, choose the sheet, rate with the keyboard, click "Download ratings CSV";
  * or import the sheet into Google Sheets, add dropdowns, and download it as CSV.
Either way, save the result as outputs/ratings_<lang>.csv and run:  python tools/tie_out.py --lang <lang> --quiet
Ratings are done by a human who speaks the language. An AI never picks the verdict.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

MAIN_SYSTEM = "nllb600m"
SHEET_COLS = ["sentence_id", "lang", "system", "src_en", "translation", "verdict", "error_type",
              "corrected_translation", "note", "rater_id"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Make the blind rating sheet for one language.")
    ap.add_argument("--lang", required=True, choices=["hi", "zh", "ar"])
    ap.add_argument("--outputs", default="outputs", help="folder (inside the repo) holding the CSVs")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    src = root / args.outputs / f"translations_{args.lang}.csv"
    if not src.exists():
        sys.exit(f"{src} not found. Run src/translate.py --lang {args.lang} first.")
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["system"] == MAIN_SYSTEM]
    if not rows:
        sys.exit(f"No '{MAIN_SYSTEM}' rows in {src.name}.")

    out = root / args.outputs / f"RATE_ME_{args.lang}.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:  # no back_translation column on purpose
            w.writerow({**r, "verdict": "", "error_type": "", "corrected_translation": "", "note": "", "rater_id": ""})
    print(f"wrote {out} ({len(rows)} rows). Next: open tools/rate.html and choose this file.")


if __name__ == "__main__":
    main()
