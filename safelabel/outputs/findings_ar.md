# Person A (Arabic): status and findings

> Fill the brackets only after the human ratings and the merged results exist.
> This project is a prototype and is not medical advice.

## Status for the lead (H)
| Item | State |
| --- | --- |
| `outputs/translations_ar.csv` | Done. 60 rows, real NLLB-200 distilled 600M output. `tie_out.py --lang ar --stage translations` prints ALL CONTROL TOTALS TIE |
| `src/evaluate.py` | Done. On `outputs_dummy` every output file exists and all 24 TIE lines show Diff = 0. Not yet run on real data |
| `outputs/RATE_ME_ar.csv` | Blind rating sheet (no back-translation). **Ratings not done yet: they must be done by a human Arabic speaker** |
| `data/lexicons/negation_ar.json` | Not reviewed yet (needs the Arabic speaker) |
| Kurmanji (extra) | `outputs/translations_kmr.csv` + `RATE_ME_kmr.csv`, made by `src/translate_kmr.py`. Not in CONTRACT.md: see below |

## About Kurmanji (extra, exploratory)
Kurmanji (Northern Kurdish, Latin script) is a language free translators serve poorly, which is the
Languages track's own focus. It is NOT one of the three main languages in CONTRACT.md, so:
- its rows use `lang = kmr` and live in their own files;
- `tools/tie_out.py` only knows `hi, zh, ar`, so Kurmanji ratings will not merge into `master.csv`
  unless H adds `kmr` to `LANGS` there (H owns that file);
- `src/evaluate.py` already reports any extra language separately and never mixes it into the
  pooled three-language results.
Kurmanji is only worth reporting if a Kurmanji speaker rates it by hand.

## Findings (fill after ratings)
- Unsafe Arabic translations: [x]/60 ([y]%, 95% interval [lo] to [hi]).
- Most common error types: [ ].
- Checks on held-out Arabic test sentences: number rule caught [ ] of [ ], negation rule [ ] of [ ],
  round-trip chrF [ ] of [ ].
- Script and dialect: translations are Modern Standard Arabic; [note anything the rater saw].

## Three failure examples (from failures.csv)
1. English: [ ] · Machine: [ ] · Correct: [ ] · Why we think it was missed: [ ]
2. [ ]
3. [ ]
