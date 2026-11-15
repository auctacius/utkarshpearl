#!/usr/bin/env python3
"""
tie_out.py -- the "do our files add up?" checker and merger (standard library only).

Run it before you push (self-check) and at Gate 3 (merge everybody's files).

    python tools/tie_out.py --lang hi --stage translations   # Gate 1: only the translation file
    python tools/tie_out.py --lang hi                        # Gate 2: translations + ratings for one language
    python tools/tie_out.py --all --write                    # Gate 3: check all languages, write outputs/master.csv
    python tools/tie_out.py --all --stage features           # Gate 3b: also check outputs/features.csv

It prints   TIE: ... Diff = 0   when a control total matches and   GAP: ... Diff = X   when it does not.
Exit code 0 = everything ties. Exit code 1 = at least one GAP (fix it before merging).
Use  --outputs outputs_dummy  to work on fake data (see tools/make_dummy.py).
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

# ---- the shared contract (keep in sync with CONTRACT.md) -----------------------------------
LANGS = ("hi", "zh", "ar")
MAIN_SYSTEM = "nllb600m"
VERDICTS = ("safe", "minor", "unsafe")
ERROR_TYPES = ("none", "number", "unit", "negation", "drug_name", "missing_info",
               "added_info", "wrong_meaning", "other")
TRANSLATION_COLS = ["sentence_id", "lang", "system", "src_en", "translation",
                    "back_translation", "model_name", "created_utc"]
RATING_COLS = ["sentence_id", "lang", "system", "verdict", "error_type",
               "corrected_translation", "note", "rater_id"]
MASTER_COLS = ["sentence_id", "lang", "system", "category", "split", "src_en", "translation",
               "back_translation", "verdict", "error_type", "corrected_translation", "note",
               "rater_id", "unsafe"]
FEATURE_COLS = ["sentence_id", "lang", "system", "src_numbers", "tgt_numbers", "num_missing",
                "num_extra", "number_flag", "src_neg", "tgt_neg", "negation_flag",
                "any_rule_flag", "rt_chrf", "labse_cos"]


class Report:
    """Prints TIE / GAP lines and counts the gaps."""

    def __init__(self, quiet: bool = False) -> None:
        self.gaps = 0
        self.quiet = quiet  # quiet = print only GAP lines (handy when pasting output to an AI tool)

    def tie(self, label: str, left: int, right: int) -> None:
        diff = left - right
        if diff == 0:
            if not self.quiet:
                print(f"TIE: {label}: {left} = {right}, Diff = 0")
        else:
            self.gaps += 1
            print(f"GAP: {label}: {left} vs {right}, Diff = {diff}")

    def gap(self, message: str) -> None:
        self.gaps += 1
        print(f"GAP: {message}")


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    """Read a CSV (UTF-8, with or without BOM). Strips spaces and skips blank rows."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = [(h or "").strip() for h in (reader.fieldnames or [])]
        rows = []
        for raw in reader:
            row = {(k or "").strip(): (v.strip() if isinstance(v, str) else "") for k, v in raw.items() if k}
            if row.get("sentence_id"):
                rows.append(row)
    return header, rows


def load_sentences(root: Path, report: Report) -> dict[str, dict]:
    path = root / "data" / "sentences_en.csv"
    _, rows = read_rows(path)
    ids = [r["sentence_id"] for r in rows]
    report.tie("sentences_en.csv duplicate ids", len(ids) - len(set(ids)), 0)
    return {r["sentence_id"]: r for r in rows}


def load_translations(outputs: Path, lang: str, valid_ids: set[str], report: Report) -> list[dict]:
    path = outputs / f"translations_{lang}.csv"
    if not path.exists():
        report.gap(f"{lang}: {path.name} not found in {outputs}")
        return []
    header, rows = read_rows(path)
    absent = [c for c in TRANSLATION_COLS if c not in header]
    if absent:
        report.gap(f"{lang}: {path.name} is missing columns {absent}")
        return []
    report.tie(f"{lang} translation rows with wrong lang code", sum(r["lang"] != lang for r in rows), 0)
    keys = Counter((r["sentence_id"], r["system"]) for r in rows)
    report.tie(f"{lang} duplicate (sentence_id, system) rows", sum(c - 1 for c in keys.values() if c > 1), 0)
    report.tie(f"{lang} translation rows with unknown sentence_id", sum(r["sentence_id"] not in valid_ids for r in rows), 0)
    report.tie(f"{lang} empty translations", sum(not r["translation"] for r in rows), 0)
    main = [r for r in rows if r["system"] == MAIN_SYSTEM]
    report.tie(f"{lang} {MAIN_SYSTEM} translation rows vs sentences_en rows", len(main), len(valid_ids))
    report.tie(f"{lang} {MAIN_SYSTEM} sentence_ids missing", len(valid_ids - {r['sentence_id'] for r in main}), 0)
    return rows


def load_ratings(outputs: Path, lang: str, trans: list[dict], report: Report) -> list[dict]:
    path = outputs / f"ratings_{lang}.csv"
    if not path.exists():
        report.gap(f"{lang}: {path.name} not found in {outputs}")
        return []
    header, rows = read_rows(path)
    absent = [c for c in RATING_COLS if c not in header]
    if absent:
        report.gap(f"{lang}: {path.name} is missing columns {absent}")
        return []
    for r in rows:  # forgive capital letters / stray spaces from the spreadsheet
        r["verdict"] = r["verdict"].lower()
        r["error_type"] = r["error_type"].lower()
    t_by_key = {(t["sentence_id"], t["system"]): t for t in trans}
    keys = Counter((r["sentence_id"], r["system"]) for r in rows)
    report.tie(f"{lang} duplicate rating rows", sum(c - 1 for c in keys.values() if c > 1), 0)
    report.tie(f"{lang} ratings with no matching translation row", sum(k not in t_by_key for k in keys), 0)
    report.tie(f"{lang} rating rows with wrong lang code", sum(r["lang"] != lang for r in rows), 0)
    main_t = sum(1 for t in trans if t["system"] == MAIN_SYSTEM)
    main_r = sum(1 for r in rows if r["system"] == MAIN_SYSTEM)
    report.tie(f"{lang} {MAIN_SYSTEM} rating rows vs translation rows", main_r, main_t)
    report.tie(f"{lang} verdicts not in {VERDICTS}", sum(r["verdict"] not in VERDICTS for r in rows), 0)
    report.tie(f"{lang} error_types not in the allowed list", sum(r["error_type"] not in ERROR_TYPES for r in rows), 0)
    report.tie(f"{lang} 'safe' rows whose error_type is not 'none'", sum(r["verdict"] == "safe" and r["error_type"] != "none" for r in rows), 0)
    report.tie(f"{lang} minor/unsafe rows with error_type 'none'", sum(r["verdict"] in ("minor", "unsafe") and r["error_type"] == "none" for r in rows), 0)
    report.tie(f"{lang} 'unsafe' rows without corrected_translation", sum(r["verdict"] == "unsafe" and not r["corrected_translation"] for r in rows), 0)
    report.tie(f"{lang} rows without rater_id", sum(not r["rater_id"] for r in rows), 0)
    if "translation" in header:  # catches accidental edits of the translation column
        changed = sum(1 for r in rows if (r["sentence_id"], r["system"]) in t_by_key
                      and r["translation"] != t_by_key[(r["sentence_id"], r["system"])]["translation"])
        report.tie(f"{lang} rating rows whose translation text differs from the translations file", changed, 0)
    return rows


def join_master(trans: list[dict], ratings: list[dict], sentences: dict[str, dict]) -> list[dict]:
    """One row per rated translation: sentence info + translation + human rating."""
    t_by_key = {(t["sentence_id"], t["system"]): t for t in trans}
    out = []
    for r in ratings:
        t = t_by_key.get((r["sentence_id"], r["system"]))
        meta = sentences.get(r["sentence_id"])
        if t is None or meta is None:
            continue  # already reported as a GAP
        out.append({
            "sentence_id": r["sentence_id"], "lang": r["lang"], "system": r["system"],
            "category": meta["category"], "split": meta["split"], "src_en": t["src_en"],
            "translation": t["translation"], "back_translation": t["back_translation"],
            "verdict": r["verdict"], "error_type": r["error_type"],
            "corrected_translation": r["corrected_translation"], "note": r["note"],
            "rater_id": r["rater_id"], "unsafe": "1" if r["verdict"] == "unsafe" else "0",
        })
    return out


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def check_features(outputs: Path, master: list[dict], report: Report) -> None:
    path = outputs / "features.csv"
    if not path.exists():
        report.gap(f"features.csv not found in {outputs}")
        return
    header, rows = read_rows(path)
    absent = [c for c in FEATURE_COLS if c not in header]
    if absent:
        report.gap(f"features.csv is missing columns {absent}")
        return
    report.tie("features rows vs master rows", len(rows), len(master))
    f_keys = {(r["sentence_id"], r["lang"], r["system"]) for r in rows}
    m_keys = {(r["sentence_id"], r["lang"], r["system"]) for r in master}
    report.tie("master keys missing from features", len(m_keys - f_keys), 0)
    for col in ("number_flag", "negation_flag", "any_rule_flag"):
        report.tie(f"features.{col} values not 0/1", sum(r[col] not in ("0", "1") for r in rows), 0)


def run(root: Path, outputs_name: str = "outputs", langs=LANGS, stage: str = "full",
        write: bool = False, quiet: bool = False) -> int:
    report = Report(quiet)
    outputs = root / outputs_name
    sentences = load_sentences(root, report)
    valid_ids = set(sentences)
    print(f"-- sentences_en.csv has {len(valid_ids)} sentences; checking {', '.join(langs)} in {outputs_name}/ (stage: {stage})")
    master: list[dict] = []
    rating_rows_total = 0
    for lang in langs:
        trans = load_translations(outputs, lang, valid_ids, report)
        if stage == "translations":
            continue
        ratings = load_ratings(outputs, lang, trans, report) if trans else []
        rating_rows_total += len(ratings)
        rows = join_master(trans, ratings, sentences)
        master.extend(rows)
        main = [r for r in rows if r["system"] == MAIN_SYSTEM]
        counts = Counter(r["verdict"] for r in main)
        n = len(main) or 1
        print(f"   {lang}: n={len(main)}  safe={counts['safe']}  minor={counts['minor']}  "
              f"unsafe={counts['unsafe']} ({100 * counts['unsafe'] / n:.1f}% unsafe)")
    if stage != "translations":
        report.tie("master rows vs total rating rows", len(master), rating_rows_total)
        if write and report.gaps == 0:
            write_csv(outputs / "master.csv", MASTER_COLS, sorted(master, key=lambda r: (r["lang"], r["system"], r["sentence_id"])))
            print(f"-- wrote {outputs / 'master.csv'} ({len(master)} rows)")
        elif write:
            print("-- NOT writing master.csv because of the GAP lines above")
    if stage == "features":
        check_features(outputs, master, report)
    print("== ALL CONTROL TOTALS TIE" if report.gaps == 0 else f"== {report.gaps} GAP(S) - fix before merging")
    return 1 if report.gaps else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Check and merge the SafeLabel CSV files.")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="repo root")
    ap.add_argument("--outputs", default="outputs", help="folder (inside root) holding the CSVs")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--lang", choices=LANGS, help="check one language")
    group.add_argument("--all", action="store_true", help="check every language")
    ap.add_argument("--stage", choices=("translations", "full", "features"), default="full")
    ap.add_argument("--write", action="store_true", help="write outputs/master.csv when everything ties")
    ap.add_argument("--quiet", action="store_true", help="print only GAP lines and the summary")
    args = ap.parse_args()
    langs = LANGS if args.all else (args.lang,)
    sys.exit(run(Path(args.root), args.outputs, langs, args.stage, args.write, args.quiet))


if __name__ == "__main__":
    main()
