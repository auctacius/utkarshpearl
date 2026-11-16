# CONTRACT — the one page every teammate and every AI tool must follow

Working title: **SafeLabel**. Track: **AI + Languages**.
Every output and write-up carries: *This project is a prototype and is not medical advice.*

## 1. The question we answer
1. How often does a free machine translator (NLLB-200 distilled 600M) turn a medicine-label sentence into
   something **unsafe** in Hindi, Chinese and Arabic, as judged by a speaker of that language?
2. Does a generic quality score (round-trip chrF) warn about those errors? Do simple number/negation
   checks warn better? What do both miss?

Hypotheses, written down BEFORE we see results (we report the outcome even if we are wrong):
- **H1** The unsafe rate is above zero in every language and differs between languages.
- **H2** Round-trip chrF is only weakly related to the human verdict and misses many unsafe translations.
- **H3** Number/negation checks catch some unsafe translations that chrF misses, at the cost of false alarms.

## 2. Languages, owners, default tools (swap freely if someone has access to more tools)
| code | language | owner | default AI tool |
|---|---|---|---|
| `hi` | Hindi | Person H (lead) | Claude + ChatGPT/Codex |
| `zh` | Chinese (Simplified unless the rater chooses Traditional) | Person C | Codex |
| `ar` | Arabic (Modern Standard) | Person A | Claude |

## 3. Who may edit what (disjoint files = no merge conflicts)
| Path | Owner |
|---|---|
| `CONTRACT.md`, `PLAN.md`, `README.md`, `AGENTS.md`, `briefs/`, `tools/`, `data/sentences_en.csv`, `data/RATING_GUIDE.md`, `src/translate.py` | H (frozen after kickoff; H announces any change) |
| `outputs/translations_hi.csv`, `outputs/ratings_hi.csv`, `data/lexicons/negation_hi.json`, `outputs/findings_hi.md` | H |
| the same four files for `zh` | C |
| the same four files for `ar` | A |
| `src/safelabel/checks.py`, `tests/test_checks.py`, `src/run_checks.py`, `src/baseline_labse.py` (stretch) | C |
| `src/evaluate.py`, `outputs/results_*.csv`, `outputs/failures.csv`, `outputs/thresholds.json`, `outputs/figures/` | A |
| `src/safelabel/predict.py`, `app/app.py`, `notebooks/` | H |
| `outputs/master.csv` (made by `tools/tie_out.py --write`), `outputs/features.csv` (made by `src/run_checks.py`) | generated — never hand-edit |

## 4. Data schemas
All CSV, UTF-8, one header row. **Read with `encoding="utf-8-sig"`, write plain UTF-8.** Language codes: `hi`, `zh`, `ar`.
Main translation system = `nllb600m`. (Stretch systems, e.g. `gemini`, use another name and are never mixed into main results.)

**`data/sentences_en.csv`** (frozen, 60 rows) — `sentence_id` (S001–S060), `category`, `split` (`dev`/`test`, 30 each),
`src_en`, `expected_numbers_en` (pipe-separated, hand-checked), `has_negation_en` (0/1, hand-checked).
All sentences are synthetic label-style text; drug names are made up.

**`outputs/translations_<lang>.csv`** (made by `src/translate.py`) —
`sentence_id, lang, system, src_en, translation, back_translation, model_name, created_utc`. Key = (`sentence_id`, `system`). 60 rows per language for `nllb600m`.

**`outputs/ratings_<lang>.csv`** (made by the human rater; extra columns such as `src_en`/`translation` are allowed) —
`sentence_id, lang, system, verdict, error_type, corrected_translation, note, rater_id`
- `verdict` ∈ `safe | minor | unsafe`
- `error_type` ∈ `none | number | unit | negation | drug_name | missing_info | added_info | wrong_meaning | other`
- `safe` ⇔ `none`; `minor`/`unsafe` need a real error type; `unsafe` needs a `corrected_translation`.

**`outputs/master.csv`** (generated) — `sentence_id, lang, system, category, split, src_en, translation, back_translation, verdict, error_type, corrected_translation, note, rater_id, unsafe` (`unsafe` = 1 if verdict is `unsafe`).

**`outputs/features.csv`** (made by `src/run_checks.py`, one row per master row) —
`sentence_id, lang, system, src_numbers, tgt_numbers, num_missing, num_extra, number_flag, src_neg, tgt_neg, negation_flag, any_rule_flag, rt_chrf, labse_cos`
- numbers are pipe-joined, formatted with `%g`; flags are `0`/`1`
- `rt_chrf` = sacrebleu sentence chrF (0–100) with `src_en` as the reference and `back_translation` as the hypothesis
- `labse_cos` stays empty unless stretch S1 is done

**`outputs/thresholds.json`** (made by `src/evaluate.py`) — `{"rt_chrf": <float>, "labse_cos": <float|null>, "chosen_on": "dev"}`

The column lists also live in code: `tools/tie_out.py` (`TRANSLATION_COLS`, `RATING_COLS`, `MASTER_COLS`, `FEATURE_COLS`). Keep them in sync.

## 5. Evaluation protocol (frozen — do not change after seeing results)
- Unit = one (sentence, language) row, main system only. Positive class = `unsafe`.
- Splits come from `sentences_en.csv`; a sentence has the same split in every language (no leakage across languages).
  **Thresholds are chosen on `dev` only. Every detector number we report is from `test` only.**
  The headline "unsafe rate per language" uses all 60 sentences (it needs no threshold).
- Detectors: `always_safe` (never flags — the do-nothing baseline), `rt_chrf` (flag if below the threshold),
  `labse` (stretch), `number_rule`, `negation_rule`, `rules` (number OR negation), `rules_plus_chrf` (rules OR chrF flag).
- Threshold rule: one global threshold for all languages, the value that maximizes F1 for `unsafe` on dev (ties → higher recall).
- Report for each detector, pooled and per language: `tp, fp, fn, tn, precision, recall, f1, flag_rate`, and
  false alarms per 10 non-unsafe rows. Always print counts next to percentages (n is small).
  95% intervals: bootstrap over `sentence_id` (1,000 resamples, seed 0).
- Spearman correlation between `rt_chrf` and the ordinal verdict (safe 0, minor 1, unsafe 2), per language.
- Control totals: for each detector `tp+fp+fn+tn` must equal the number of test rows → print `TIE: ... Diff = 0`.
- `outputs/failures.csv`: every unsafe row that `rules_plus_chrf` missed (false negatives) and every non-unsafe row it flagged
  (false alarms), with `src_en, translation, corrected_translation, error_type`.
- Never report numbers from `outputs_dummy/`.

## 6. Function contracts
```python
# src/safelabel/checks.py  (exists, tested; owner C may extend, must keep these signatures)
extract_numbers(text: str, lang: str = "en", use_words: bool = False) -> list[float]   # sorted, unique
number_check(src_en, tgt, lang) -> {"src_numbers","tgt_numbers","missing","extra","flag"}
has_negation(text, lang) -> bool
negation_check(src_en, tgt, lang) -> {"src_neg","tgt_neg","flag"}
run_all_checks(src_en, tgt, lang) -> {..., "number_flag","negation_flag","any_rule_flag"}

# src/run_checks.py  (C)   CLI: python src/run_checks.py --outputs outputs
#   reads <outputs>/master.csv, writes <outputs>/features.csv, prints "TIE: features rows vs master rows"

# src/evaluate.py  (A)     CLI: python src/evaluate.py --outputs outputs
#   writes results_by_lang.csv, results_detectors.csv, results_error_types.csv, results_correlation.csv,
#          failures.csv, thresholds.json, figures/*.png   (column names in briefs/BRIEF_arabic_eval.md)

# src/safelabel/predict.py (H)
check_translation(src_en: str, lang: str, translator=None, thresholds=None, scorer=None) -> dict   # scorer(src_en, back) -> chrF
#   keys: lang, src_en, translation, back_translation, verdict ("dont_rely"|"unsure"|"looks_consistent"),
#         reasons (list[str]), rt_chrf, checks (run_all_checks output), next_step, disclaimer
#   The app never says "safe". Best verdict text: "no problems found by our checks - still confirm with your pharmacist".

# app/app.py (H)
build_demo() -> gradio Blocks/Interface      # notebooks/SafeLabel_final.ipynb calls build_demo().launch()
# outputs/demo_cache.json (H): a JSON list of check_translation() results for the 6 chosen demo examples;
#   the notebook shows them without a GPU (switch REFRESH_CACHE in notebook section 7a to rebuild it)
```

## 7. Gates — "done" means these commands print `ALL CONTROL TOTALS TIE`
| Gate | CT clock | Command / evidence |
|---|---|---|
| G1 | 11:45 AM | `python tools/tie_out.py --lang <L> --stage translations --quiet` and `outputs/translations_<L>.csv` pushed |
| G2 | 2:30 PM | `python tools/tie_out.py --lang <L> --quiet` (ratings tie) + `python -m unittest discover -s tests` green + lexicon reviewed |
| G3 | 4:30 PM | H: `python tools/tie_out.py --all --write --quiet` → C: `python src/run_checks.py` → `python tools/tie_out.py --all --stage features --quiet` → A: `python src/evaluate.py` |
| G4 | 6:00 PM | numbers frozen (git tag `results-v1`), README filled, final notebook passes *Run all* in a fresh Colab runtime |

## 8. House rules
1. Only edit files you own. Pull before you push: `git pull --rebase`.
2. **Ratings are human-only.** An AI may look a word up for you; it never picks a verdict. Disclose AI tools in the write-up.
3. Comment code in plain language: every teammate must be able to explain every cell to the judges.
4. No API keys in files. No real patient or prescription text anywhere — synthetic sentences only.
5. Never regenerate `translations_<L>.csv` after rating has started.
6. Windows: set `PYTHONUTF8=1` before running Python. Excel can garble Arabic/Chinese CSVs — use Google Sheets.
7. Stuck for 20 minutes? Send the lead the last 30 lines of the error, not the whole file.
8. Report honest results, including weak ones. Do not tune on `test`.
