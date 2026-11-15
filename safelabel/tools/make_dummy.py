#!/usr/bin/env python3
"""
make_dummy.py -- make FAKE translations, ratings, master.csv and features.csv so everybody can
build and test their part before the real data exists. Standard library only.

    python tools/make_dummy.py            # writes into outputs_dummy/

!!! NEVER quote numbers from outputs_dummy/ anywhere. The ratings are random and the "translations"
    are just the English with a language tag. This only proves the plumbing works.
"""
from __future__ import annotations

import difflib
import random
import sys
from pathlib import Path

import tie_out as T  # the shared contract lives in tie_out.py (same folder)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from safelabel import checks  # noqa: E402


def corrupt(text: str, kind: str, rng: random.Random) -> str | None:
    """Break a sentence in a believable way. Returns None if that kind of break is impossible."""
    if kind == "number":
        spots = [i for i, c in enumerate(text) if c.isdigit()]
        if not spots:
            return None
        i = rng.choice(spots)
        return text[:i] + str((int(text[i]) + rng.randint(1, 3)) % 10) + text[i + 1:]
    if kind == "negation":
        for cue in ("Do not ", "do not ", "Avoid ", "avoid ", "Not ", "not "):
            if cue in text:
                return text.replace(cue, "", 1)
        return None
    return text[: max(5, len(text) // 2)]  # missing_info: cut the sentence in half


def main() -> None:
    out = ROOT / "outputs_dummy"
    _, sentences = T.read_rows(ROOT / "data" / "sentences_en.csv")
    rng = random.Random(7)
    for lang in T.LANGS:
        trans, rate = [], []
        for s in sentences:
            src = s["src_en"]
            roll = rng.random()
            if roll < 0.22:  # pretend the translator made an unsafe mistake
                kind = rng.choice(["number", "negation", "missing_info"])
                broken = corrupt(src, kind, rng)
                if broken is None:
                    kind, broken = "missing_info", corrupt(src, "missing_info", rng)
                verdict, error = "unsafe", kind
            elif roll < 0.35:
                broken, verdict, error = src, "minor", "other"
            else:
                broken, verdict, error = src, "safe", "none"
            row = {"sentence_id": s["sentence_id"], "lang": lang, "system": T.MAIN_SYSTEM, "src_en": src,
                   "translation": f"[{lang}] {broken}", "back_translation": broken,
                   "model_name": "DUMMY", "created_utc": "2026-01-01T00:00:00+00:00"}
            trans.append(row)
            rate.append({"sentence_id": s["sentence_id"], "lang": lang, "system": T.MAIN_SYSTEM,
                         "verdict": verdict, "error_type": error,
                         "corrected_translation": f"[{lang}] {src}" if verdict == "unsafe" else "",
                         "note": "dummy", "rater_id": f"dummy_{lang}"})
        T.write_csv(out / f"translations_{lang}.csv", T.TRANSLATION_COLS, trans)
        T.write_csv(out / f"ratings_{lang}.csv", T.RATING_COLS, rate)

    code = T.run(ROOT, "outputs_dummy", T.LANGS, "full", write=True)
    if code:
        sys.exit(code)

    # Fake feature file: real rule checks + a stand-in for round-trip chrF (difflib similarity x 100).
    _, master = T.read_rows(out / "master.csv")
    feats = []
    for r in master:
        c = checks.run_all_checks(r["src_en"], r["translation"], r["lang"])
        feats.append({
            "sentence_id": r["sentence_id"], "lang": r["lang"], "system": r["system"],
            "src_numbers": "|".join(f"{v:g}" for v in c["src_numbers"]),
            "tgt_numbers": "|".join(f"{v:g}" for v in c["tgt_numbers"]),
            "num_missing": "|".join(f"{v:g}" for v in c["missing"]),
            "num_extra": "|".join(f"{v:g}" for v in c["extra"]),
            "number_flag": int(c["number_flag"]), "src_neg": int(c["src_neg"]), "tgt_neg": int(c["tgt_neg"]),
            "negation_flag": int(c["negation_flag"]), "any_rule_flag": int(c["any_rule_flag"]),
            "rt_chrf": round(difflib.SequenceMatcher(None, r["src_en"], r["back_translation"]).ratio() * 100, 1),
            "labse_cos": "",
        })
    T.write_csv(out / "features.csv", T.FEATURE_COLS, feats)
    print(f"-- wrote {out / 'features.csv'} ({len(feats)} rows). DUMMY DATA: never quote these numbers.")


if __name__ == "__main__":
    main()
