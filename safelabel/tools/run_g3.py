#!/usr/bin/env python3
"""
run_g3.py -- the whole Gate-3 merge in ONE command (standard library only). Owner: Person H.

    python tools/run_g3.py                          # real data in outputs/
    python tools/run_g3.py --outputs outputs_dummy  # rehearsal on fake data (NEVER quote those numbers)

It runs these steps in order and stops at the first problem, telling you which step failed:
  1. tools/tie_out.py --all --write        check every language's translations + ratings, write master.csv
  2. src/run_checks.py                     number check, negation check, round-trip chrF  ->  features.csv
  3. tools/tie_out.py --all --stage features   check features.csv against master.csv
  4. src/evaluate.py                       results tables, failures, thresholds.json, figures

Needs:  pip install sacrebleu pandas scipy matplotlib   (everything except sacrebleu is already in Colab).
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_step(number: int, title: str, command: list[str]) -> None:
    print(f"\n=== STEP {number}: {title}\n    $ {' '.join(command)}", flush=True)
    env = {**os.environ, "PYTHONUTF8": "1"}
    result = subprocess.run(command, cwd=ROOT, env=env)
    if result.returncode != 0:
        sys.exit(f"\nSTOPPED at step {number} ({title}). Fix the GAP / error above, then run this command again.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the whole Gate-3 merge, check and evaluation.")
    ap.add_argument("--outputs", default="outputs", help="folder (inside the repo) with the CSVs")
    args = ap.parse_args()
    py = sys.executable

    if importlib.util.find_spec("sacrebleu") is None:
        sys.exit("sacrebleu is not installed (needed for the chrF score). Run:  pip install sacrebleu")

    run_step(1, "check every language and write master.csv",
             [py, "tools/tie_out.py", "--all", "--write", "--quiet", "--outputs", args.outputs])
    run_step(2, "number check, negation check and round-trip chrF",
             [py, "src/run_checks.py", "--outputs", args.outputs])
    run_step(3, "check features.csv against master.csv",
             [py, "tools/tie_out.py", "--all", "--stage", "features", "--quiet", "--outputs", args.outputs])
    run_step(4, "evaluation: tables, failures, thresholds, figures",
             [py, "src/evaluate.py", "--outputs", args.outputs])

    print(f"\nG3 DONE. master.csv, features.csv, results_*.csv, failures.csv, thresholds.json and figures/ are in {args.outputs}/")
    if "dummy" in args.outputs:
        print("!!! These came from FAKE data. Never quote them.")
    else:
        print("Next: choose 6 demo examples, refresh the demo cache (notebook section 7a), fill the README numbers, tag results-v1.")


if __name__ == "__main__":
    main()
