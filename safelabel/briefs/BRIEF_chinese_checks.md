# Brief — Person C (Chinese speaker · default tool: Codex)

You own: **language `zh`** (translate, rate, lexicon, findings) and the **checks code** (`checks.py`, `run_checks.py`).
Give your AI tool: `AGENTS.md` + `CONTRACT.md` + this file. Nothing else (saves tokens).

## Your timeline (Central Time; shift together if you start late, but keep the gate times)
| When | Task | You produce |
|---|---|---|
| 11:00–11:45 | **C1 Translate.** Get the repo (clone or unzip) into Colab, GPU runtime. `!pip -q install transformers sentencepiece sacrebleu` → `!python src/translate.py --lang zh --limit 5` → `!python src/translate.py --lang zh`. Default is Simplified; for Traditional add `--zh-script hant` (say which in the write-up). Download the CSV into `outputs/` and push. | `outputs/translations_zh.csv` · **G1** |
| 11:45–1:30 | **C2 Rate** all 60 rows exactly as `data/RATING_GUIDE.md` says (blind: no back-translation, no checker output). You are the "real speaker" check. | `outputs/ratings_zh.csv` |
| 1:30–2:15 | **C3 Lexicon.** Open `data/lexicons/negation_zh.json` (a STARTER list). Look at your own rows with `negation` errors and at correct translations of "do not/avoid" sentences. Add cues you see, delete cues that cause false alarms. Add 3 Chinese test sentences to `tests/test_checks.py`. | reviewed lexicon |
| 2:15–2:30 | **G2.** `python tools/tie_out.py --lang zh --quiet` and `python -m unittest discover -s tests` must both be clean. Push. | · **G2** |
| 2:30–3:15 | **C4 `src/run_checks.py`** (spec below). Build it on fake data: `python tools/make_dummy.py`, then `python src/run_checks.py --outputs outputs_dummy`. | `src/run_checks.py` |
| 3:15–4:15 | **C5 Harden `checks.py` on your REAL zh rows.** Run the checker over your rows; list every row where the checker and your rating disagree; fix extraction bugs (Chinese numerals like 两/半/一次 are the big one) and add a unit test per fix. | extra tests |
| 4:30 | **G3.** After H writes `outputs/master.csv`: `python src/run_checks.py` → `python tools/tie_out.py --all --stage features --quiet`. Push `outputs/features.csv`. | · **G3** |
| 4:30–6:00 | Stretch in order: **S1** LaBSE baseline, **S4** target-side number words (`extract_numbers(..., use_words=True)` — enable the skipped test). Then write `outputs/findings_zh.md`: 5 sentences on what went wrong in Chinese + 3 best failure examples (English / machine / your correction). Ask a *different* AI tool to suggest 10 extra edge-case tests for `extract_numbers`, keep the good ones. | `findings_zh.md` |

## `src/run_checks.py` spec
CLI `python src/run_checks.py [--outputs outputs]`. Reads `<outputs>/master.csv`. For every row call
`safelabel.checks.run_all_checks(src_en, translation, lang)` and compute `rt_chrf` with
`from sacrebleu.metrics import CHRF; CHRF().sentence_score(back_translation, [src_en]).score`.
Writes `<outputs>/features.csv` with exactly the columns in CONTRACT §4 (`labse_cos` left empty), numbers pipe-joined with `%g`, flags as 0/1.
Prints `TIE: features rows vs master rows: N = N, Diff = 0`. Plain-language comments on every function.

## Acceptance
- `python -m unittest discover -s tests -v` is green (36 tests; 1 stretch test skipped until you implement it).
- `python tools/tie_out.py --all --stage features --quiet` ends with `ALL CONTROL TOTALS TIE`.
- You can explain, without notes, why we compare *sets* of numbers and why `no` is not an English negation cue.

## Starter prompt for Codex (paste, then work in small steps)
> Read AGENTS.md, CONTRACT.md and briefs/BRIEF_chinese_checks.md. Run the unit tests and confirm they pass.
> Task now: <C4 or C5 from the brief>. Edit files in place, run the tests after every change, and reply with a 3-line summary
> plus only the names of failing tests. Comment every function in plain language.

## Don'ts
Don't let an AI choose any rating. Don't edit files you don't own (ask H). Don't use `outputs_dummy` numbers anywhere real.
