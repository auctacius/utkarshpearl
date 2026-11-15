# PIIParity
Multilingual personal-information detection and redaction | AI + Languages

**Phase 2 runs a real pretrained multilingual GLiNER model locally**, alongside the preserved regex baseline. Compare Regex, AI and Hybrid outputs; see highlighted entities, original offsets, extracted text and redaction. Fictional examples: English, Kurmanji, Hindi, Simplified Chinese, Spanish and Turkish. Kurmanji is experimental. No language has independently validated accuracy yet.

## Launch (Python 3.12 recommended)
From the repository root:
```sh
cd "Adam's GPT"
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python experiments/download_model.py
PYTHONPATH=src python -m piiparity.app
```
Open http://127.0.0.1:7860 . The first prediction loads the model; subsequent short paragraphs were much faster on the tested Mac. Model download is about 1.16 GB plus tokenizer; no API key required. Downloads occur only in the explicit setup step; weights are excluded from Git. If the project is moved, rerun download_model.py to update local paths. For other platforms, requirements-ai.txt supplies the primary version pins if the tested full lock cannot resolve; re-record and test the resulting environment.

Already installed here: `PYTHONPATH=src .venv/bin/python -m piiparity.app`.

## Verify and reproduce
```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python experiments/phase2_smoke.py
# With the Gradio server running:
PYTHONPATH=src python experiments/verify_ui.py
printf 'Mira Patel lives in London. Email mira@example.com.' | PYTHONPATH=src python -m piiparity redact --mode Hybrid --language en
```
The first command runs 35 regression tests, including the original 16. The smoke script executes real inference and writes diagnostic reports. The UI verifier makes 11 live endpoint checks. These scripts use only fictional inputs. To run the original dependency-free tests alone: `PYTHONPATH=src python3 -m unittest discover -s tests -p test_pipeline.py -v`.

Baseline CLI: `PYTHONPATH=src python3 -m piiparity redact --mode Regex`; reads stdin. Baseline evaluation: `PYTHONPATH=src python3 -m piiparity evaluate data/smoke.jsonl`. Modes are case-sensitive. All offsets are Python Unicode code points, not UTF-16 browser offsets.

## Evidence and limits
Actual smoke fixture F1: Regex 0.6000; AI 0.5455; Hybrid 0.7126. **These 48 development fixtures are NOT an independent benchmark or evidence of fairness.** AI-only is weaker than regex on this tiny fixture set. Full per-language counts, failures, ground truth and predictions are in reports/phase2_*_smoke.json. Actual six-language model examples and timing are in reports/phase2_inference.json; live app checks in reports/phase2_ui_checks.json.

Known failures: missed Kurmanji surname, Turkish location over-redaction, AI email misses, false positives and unsupported phone/address formats. Short-paragraph limits are enforced rather than silently truncating. Use fictional text; this is not a safe anonymization service.

Model/license/revision: docs/MODEL.md. Setup and system design: docs/ARCHITECTURE.md. Official rules: docs/COMPLIANCE.md. Full editable history: docs/ENGINEERING_JOURNAL.md; PDF: reports/PIIParity_Engineering_Journal.pdf. Attribution: docs/CREDITS.md.

PDF regeneration: `python -m pip install -r requirements-report.txt` then `python experiments/export_journal.py`.

Phase 3 remains unstarted: independent licensed data, grouped frozen splits, fluent-speaker review and rigorous comparison. The repository remains private; public submission access and student contribution/understanding checks are still outstanding.
