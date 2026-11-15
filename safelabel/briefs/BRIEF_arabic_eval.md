# Brief — Person A (Arabic speaker · default tool: Claude)

You own: **language `ar`** (translate, rate, lexicon, findings) and the **evaluation code** (`src/evaluate.py`, figures, failures).
Give your AI tool: `AGENTS.md` + `CONTRACT.md` + this file. Nothing else (saves tokens).

## Your timeline (Central Time; keep the gate times even if you start late)
| When | Task | You produce |
|---|---|---|
| 11:00–11:45 | **A1 Translate.** Colab with GPU: `!pip -q install transformers sentencepiece sacrebleu` → `!python src/translate.py --lang ar --limit 5` → `!python src/translate.py --lang ar`. Download into `outputs/` and push. | `outputs/translations_ar.csv` · **G1** |
| 11:45–1:30 | **A2 Rate** all 60 rows exactly as `data/RATING_GUIDE.md` says (blind). You are the "real speaker" check. Note in `note` any dialect or script issue you see. | `outputs/ratings_ar.csv` |
| 1:30–2:15 | **A3 Lexicon.** Review `data/lexicons/negation_ar.json` (STARTER): add cues you see in correct "do not/avoid" translations, remove cues that cause false alarms. Add 3 Arabic tests to `tests/test_checks.py` (tell C first). | reviewed lexicon |
| 2:15–2:30 | **G2.** `python tools/tie_out.py --lang ar --quiet` clean. Push. | · **G2** |
| 2:30–4:30 | **A4 `src/evaluate.py`** built on fake data: `python tools/make_dummy.py` gives `outputs_dummy/master.csv` + `features.csv`. Run `python src/evaluate.py --outputs outputs_dummy` until every output file below exists and every `TIE:` line prints. | `src/evaluate.py` |
| 4:30–5:30 | **G3.** When H pushes real `master.csv` and C pushes `features.csv`, run `python src/evaluate.py` on the real data. Look at the numbers; do NOT change the protocol (CONTRACT §5). | `outputs/results_*.csv`, `failures.csv`, `thresholds.json`, `figures/` |
| 5:30–6:00 | **A5** Write `outputs/findings_ar.md` (5 sentences + 3 failure examples) and draft the **Results** paragraph for README (honest, counts next to percentages, which hypotheses held). | `findings_ar.md`, Results draft |

## What `evaluate.py` must write (column names are the contract)
- `results_by_lang.csv`: `lang, n, safe, minor, unsafe, unsafe_rate, unsafe_lo, unsafe_hi` (all 60 rows per language; Wilson 95% interval is fine) plus a pooled `all` row.
- `results_detectors.csv`: `detector, lang, n_test, tp, fp, fn, tn, precision, recall, f1, flag_rate, false_alarms_per_10_nonunsafe, precision_lo, precision_hi, recall_lo, recall_hi` for detectors `always_safe, rt_chrf, number_rule, negation_rule, rules, rules_plus_chrf` (+ `labse` if present) and `lang` ∈ `all, hi, zh, ar`. Test split only.
- `results_error_types.csv`: `lang, error_type, count` (main system, all 60 rows).
- `results_correlation.csv`: `lang, spearman_rho, p_value, n` for `rt_chrf` vs ordinal verdict (safe 0, minor 1, unsafe 2).
- `failures.csv`: false negatives and false alarms of `rules_plus_chrf` on test, with `lang, sentence_id, kind (FN|FP), src_en, translation, corrected_translation, error_type, verdict`.
- `thresholds.json`: `{"rt_chrf": <float>, "labse_cos": <float|null>, "chosen_on": "dev"}`.
- `figures/unsafe_rate_by_lang.png` and `figures/detector_recall_precision.png` (readable on a video: big labels, counts on bars).
- Print `TIE: <detector> <lang>: tp+fp+fn+tn = n_test, Diff = 0` for every row of `results_detectors.csv`.

## Acceptance
- On fake data **and** on real data, all files exist and all `TIE:` lines show `Diff = 0`.
- `always_safe` shows recall 0 (that is the point of the baseline).
- With ~10–20 unsafe test rows the intervals will be wide — print them and say so; that is an honest result, not a bug.
- You can explain, without notes, why the threshold is chosen on dev only and why we resample `sentence_id` instead of rows.

## Starter prompt for Claude
> Read AGENTS.md, CONTRACT.md and briefs/BRIEF_arabic_eval.md. Build src/evaluate.py exactly to the output files listed in the brief,
> using pandas/scipy/matplotlib. First run it on outputs_dummy (python tools/make_dummy.py). Comment every function in plain language.
> Reply with a short summary and any TIE line that is not Diff = 0.

## Don'ts
Don't let an AI choose any rating. Don't re-pick thresholds on test. Don't quote anything computed from `outputs_dummy/`.
