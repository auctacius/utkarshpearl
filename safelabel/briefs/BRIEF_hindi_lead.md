# Brief — Person H (Hindi speaker, lead · has Claude + ChatGPT/Codex)

You own: **language `hi`**, the **repo and merge**, the **demo app**, the **final notebook**, README, video and the submission.
Give your AI tool: `AGENTS.md` + `CONTRACT.md` + this file. Use `PLAN.md` yourself; don't paste it into AI tools.

## Your timeline (Central Time)
| When | Task | You produce |
|---|---|---|
| 11:00–11:45 | **H1 Setup + translate.** The code is in the team's shared repo `https://github.com/auctacius/utkarshpearl`, folder `safelabel/` (the repo also holds `Adam's GPT` and `Alans Claude`: never edit them). Work from a fresh clone, not from the `VeritasAIhackathon` folder (its older finance `CLAUDE.md`/`AGENTS.md` would confuse AI tools). Make sure both teammates can write to the repo (owner: Settings → Collaborators), or fall back to the zip. Send the kickoff message (PLAN §1). In Colab (GPU): `!pip -q install transformers sentencepiece sacrebleu` → `!python src/translate.py --lang hi --limit 5` → `!python src/translate.py --lang hi`. **Check that `translate.py` works first** — it was written without a GPU; if it breaks, fix it fast and tell C and A. | `outputs/translations_hi.csv` · **G1** |
| 11:45–1:30 | **H2 Rate** all 60 rows exactly as `data/RATING_GUIDE.md` says (blind). | `outputs/ratings_hi.csv` |
| 1:30–2:15 | **H3 Lexicon** `data/lexicons/negation_hi.json` review (see A3/C3 for what to do). | reviewed lexicon |
| 2:15–2:30 | **G2** `python tools/tie_out.py --lang hi --quiet`. Nudge C and A. | · **G2** |
| 2:30–4:15 | **H4 Demo on fake data.** Build `src/safelabel/predict.py` (`check_translation`, CONTRACT §6) and `app/app.py` (Gradio, exposing `build_demo()`) using `outputs_dummy/` and a stub translator that returns a canned translation. | `predict.py`, `app.py` |
| 4:30 | **G3 merge.** Pull everyone's files, then: `python tools/tie_out.py --all --write --quiet` → tell C → `python src/run_checks.py` → `python tools/tie_out.py --all --stage features --quiet` → tell A. Fix any `GAP:` by messaging the owner with the exact line. | `outputs/master.csv` · **G3** |
| 4:30–6:00 | **H5 Real demo.** Load `outputs/thresholds.json`; wire in the real NLLB translator (lazy-load, GPU if present, with a **cached-examples fallback** when the model cannot load). Pick 6 demo examples (2 per language, from `failures.csv` and clean rows). Finish `notebooks/SafeLabel_final.ipynb` — **the skeleton already exists**: follow the checklist cell at its top (set `REPO_URL`, fill every `<<...>>`, save the 6 demo results to `outputs/demo_cache.json` with its `REFRESH_CACHE` switch, then *Restart and run all*). Fill README numbers. Tag `results-v1`. | notebook, README · **G4** |
| 6:00–7:00 | **H6 Video** (script in PLAN §8). Record, upload as YouTube *unlisted* or Drive "anyone with the link". | video link |
| 7:00–8:00 | **H7 Submit v1** (checklist PLAN §9). Open every link in an incognito window. Resubmit later if you improve things. | submission |

## `predict.py` rules
- Verdict `dont_rely` if `any_rule_flag` or `rt_chrf < thresholds["rt_chrf"]`; `unsure` if `rt_chrf` is within 5 points above the threshold; otherwise `looks_consistent`.
- `reasons` are plain sentences built from the check details, e.g. "The number 6 in the English is not in the translation." / "The English says 'do not' but the translation does not seem to."
- **Never** output the word "safe". For `looks_consistent` say: "Our checks found no problems. That does not prove the translation is right — confirm with your pharmacist." `next_step` for the other verdicts: "Ask your pharmacist or doctor to confirm this instruction in your language."
- Always show the disclaimer: *This project is a prototype and is not medical advice.*

## Gradio / notebook tips
- Launch with `demo.launch()` (no blocking loop) so *Run all* finishes; wrap model loading in `try/except` and fall back to cached examples.
- The notebook must show saved outputs, contain no API keys, and run top to bottom in a fresh Colab runtime.
- Use `explainable-demo` and `finance-demo-reliability` ideas if useful (they were written for finance but the checklist applies).

## Starter prompt (Codex or Claude)
> Read AGENTS.md, CONTRACT.md and briefs/BRIEF_hindi_lead.md. Build src/safelabel/predict.py and app/app.py (Gradio) to the contract,
> working on outputs_dummy with a stub translator first. Comment every function in plain language. Reply with a short summary.

## Cross-review (15 min at G3)
Ask the *other* AI tool (Claude ↔ Codex) to read `tools/tie_out.py` and `src/safelabel/checks.py` and list the 5 most likely bugs. Fix only what is real.
