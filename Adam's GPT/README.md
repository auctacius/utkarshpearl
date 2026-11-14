# PIIParity
Multilingual Personal Information Detection and Redaction | AI + Languages

Phase 1: working **regex comparator**, not yet an AI model or submission-ready privacy tool. Six-language fictional fixtures: English, Kurmanji (Latin), Hindi, Simplified Chinese, Spanish, Turkish. It detects ASCII email addresses and international-format phone strings; names, locations, local phones and obfuscated emails can remain visible.

## Run offline (Python 3.10+)
From the repository root: `cd "Adam's GPT"`.
No third-party package is needed for detection/tests:
```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
printf 'Email student@example.com; phone +1-202-555-0100.' | PYTHONPATH=src python3 -m piiparity redact
PYTHONPATH=src python3 -m piiparity evaluate data/smoke.jsonl > reports/baseline_results.json
```
Optional installation: `python3 -m pip install -e .` then `piiparity redact`.
PDF export: install `requirements-report.txt`, then `python3 experiments/export_journal.py`.

Read docs/COMPLIANCE.md for official requirements and blockers, docs/SCHEMA_AND_EVALUATION.md for labels/scoring, data/README.md for dataset selection, docs/ARCHITECTURE.md for pipeline design, docs/CREDITS.md for AI/human attribution, and docs/ENGINEERING_JOURNAL.md for actual work. Full journal PDF: reports/PIIParity_Engineering_Journal.pdf.

Results are development smoke checks, never held-out performance or proof of cross-language parity. A trained/pretrained model, independent licensed evaluation and fluent-speaker validation remain next-phase work. Prototype only: do not use on sensitive real messages or rely on it to remove all identifying information.
