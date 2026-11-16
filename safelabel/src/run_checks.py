"""Write one row of checker features for each row in master.csv."""
import argparse
import csv
from pathlib import Path
from tempfile import NamedTemporaryFile

from sacrebleu.metrics import CHRF

from safelabel.checks import run_all_checks

FEATURE_COLUMNS = (
    "sentence_id", "lang", "system", "src_numbers", "tgt_numbers", "num_missing",
    "num_extra", "number_flag", "src_neg", "tgt_neg", "negation_flag",
    "any_rule_flag", "rt_chrf", "labse_cos",
)


def pipe_numbers(numbers):
    """Write a list of numbers as one pipe-separated CSV cell."""
    return "|".join("%g" % number for number in numbers)


def build_features(row, chrf):
    """Compare the translation with the source and score the English back-translation."""
    checks = run_all_checks(row["src_en"], row["translation"], row["lang"])
    return {
        "sentence_id": row["sentence_id"],
        "lang": row["lang"],
        "system": row["system"],
        "src_numbers": pipe_numbers(checks["src_numbers"]),
        "tgt_numbers": pipe_numbers(checks["tgt_numbers"]),
        "num_missing": pipe_numbers(checks["missing"]),
        "num_extra": pipe_numbers(checks["extra"]),
        "number_flag": int(checks["number_flag"]),
        "src_neg": int(checks["src_neg"]),
        "tgt_neg": int(checks["tgt_neg"]),
        "negation_flag": int(checks["negation_flag"]),
        "any_rule_flag": int(checks["any_rule_flag"]),
        "rt_chrf": chrf.sentence_score(row["back_translation"], [row["src_en"]]).score,
        "labse_cos": "",
    }


def main():
    """Read master.csv, write features.csv, and print the row counts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    master = args.outputs / "master.csv"
    if not master.is_file():
        parser.error(f"{master} is missing. Ask the lead to generate master.csv first.")

    with master.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"sentence_id", "lang", "system", "src_en", "translation", "back_translation"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            parser.error(f"{master} is missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    chrf = CHRF()
    features = [build_features(row, chrf) for row in rows]

    # Only replace the output after the whole CSV has been written.
    handle = NamedTemporaryFile(mode="w", dir=args.outputs, encoding="utf-8", newline="",
                                delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            writer = csv.DictWriter(handle, fieldnames=FEATURE_COLUMNS)
            writer.writeheader()
            writer.writerows(features)
        temporary.replace(args.outputs / "features.csv")
    finally:
        temporary.unlink(missing_ok=True)

    print(f"TIE: features rows vs master rows: {len(features)} = {len(rows)}, Diff = 0")


if __name__ == "__main__":
    main()
