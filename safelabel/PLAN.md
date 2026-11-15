# SafeLabel — master plan (for the whole team)

**Today:** Sun Nov 15, 2026. **Deadline: 11:59 PM ET = 10:59 PM CT.** This plan was written at 10:25 AM CT (~12.5 h left).
Times below are **Central Time (CT)** and assume kickoff at **11:00 AM CT**. If you start later, keep the gate times and cut stretch goals (§7) — never cut the human ratings.

## 0. One-minute summary
- **Pitch:** SafeLabel helps a family member who reads Hindi, Chinese or Arabic by taking an English medicine-label sentence and giving back a translation plus a warning ("don't rely on this" / "no problems found by our checks") with the reason.
- **Track:** AI + Languages. **Starting point:** brief 4.4.2 *Translation quality test* (NLLB-200). **What we added:** our own user (a family member at a pharmacy counter), our own data (60 label-style sentences), our own question (does a normal quality score catch dangerous errors?), and checks by real speakers of each language — exactly what the track's judges list as extra credit.
- **Study:** 60 sentences × 3 languages translated by NLLB-200 (free). Each of us rates the translations in our own language (`safe` / `minor` / `unsafe`). On held-out *test* sentences we compare three things: "always safe" (do-nothing baseline), a generic quality score (round-trip chrF), and simple number/negation rules. Then we show where all of them fail.
- **Deliverables:** one GitHub repo + one Colab notebook (*Run all*, outputs visible) + one-page write-up (`README.md`, official template) + a 2-minute video.
- **Honesty:** with ~60 sentences per language the numbers are small. We report counts, intervals and failures. A modest honest result beats an unexplained high one (the briefs say so).

## 1. Who does what
| Person | Language | Default tool | Packages (details in `briefs/`) |
|---|---|---|---|
| **H** (lead) | Hindi | Claude + ChatGPT/Codex | repo + merge · demo app · final notebook · README · video · submission |
| **C** | Chinese | Codex | `checks.py` owner · `run_checks.py` · LaBSE stretch |
| **A** | Arabic | Claude | `evaluate.py` · figures · failures table · Results paragraph |

Everyone also: translates their own language (45 min), **rates 60 translations by hand** (~90 min), reviews their negation word list (45 min), writes a short findings note.
Tools are defaults — if a teammate turns out to have more tools, swap freely; every brief is tool-agnostic.

**Kickoff message (copy/paste into the group chat):**
> Plan + code are in the repo/zip. Read PLAN.md §1–2 (5 min), then your brief in briefs/. In your AI tool paste ONLY: AGENTS.md + CONTRACT.md + your brief. First job: run translate for your language in Colab (GPU) and push the CSV by 11:45 AM CT. Gates: G1 11:45 AM · G2 2:30 PM · G3 4:30 PM · G4 6:00 PM (CT). Ratings are human-only: no AI picks verdicts. Stuck 20 min → send H the last 30 lines of the error.

## 2. Timeline (CT) — gates are fixed
| Clock | Gate / milestone | Evidence |
|---|---|---|
| 11:00 AM | Kickoff (10-minute call: roles, tools, who has a Colab GPU) | everyone has the repo |
| **11:45 AM** | **G1** — three translation files | `python tools/tie_out.py --lang <L> --stage translations --quiet` |
| 11:45 AM–1:30 PM | Rating block (all three in parallel) | — |
| 1:30–2:15 PM | Lexicon review; H, A: start building on fake data | — |
| **2:30 PM** | **G2** — ratings in, lexicons reviewed, tests green | `python tools/tie_out.py --lang <L> --quiet` · unit tests |
| 2:30–4:30 PM | C: `run_checks.py` + harden checks · A: `evaluate.py` · H: demo app (all on fake data) | `python tools/make_dummy.py` |
| **4:30 PM** | **G3** — merge: `master.csv` → `features.csv` → results | `tie_out --all --write`, `run_checks.py`, `tie_out --all --stage features`, `evaluate.py` |
| 4:30–6:00 PM | Real numbers, real demo, failures, README, notebook | — |
| **6:00 PM** | **G4** — results frozen (git tag `results-v1`), notebook passes *Run all* in a fresh runtime | — |
| 6:00–7:00 PM | Record video | link works in incognito |
| **8:00 PM** | **Submit v1** (9:00 PM ET) | form submitted |
| 8:00–10:00 PM | Polish + resubmit (allowed; latest version counts). **Hard stop 10:00 PM CT** | — |
| 10:59 PM CT | Deadline (11:59 PM ET) | — |

## 3. How the pieces fit
```
data/sentences_en.csv (60) ─► src/translate.py ─► outputs/translations_<L>.csv      (each person, own language)
                                      │
                      human rating in Google Sheets ─► outputs/ratings_<L>.csv      (each person)
                                      │
            tools/tie_out.py --all --write ─► outputs/master.csv                    (H, at G3)
                                      │
                        src/run_checks.py ─► outputs/features.csv                   (C)
                                      │
                         src/evaluate.py ─► outputs/results_*.csv, failures.csv, thresholds.json, figures/   (A)
                                      │
     src/safelabel/predict.py + app/app.py ─► Gradio demo · notebooks/SafeLabel_final.ipynb                  (H)
```
**Why nobody waits:** `python tools/make_dummy.py` writes fake-but-correctly-shaped files into `outputs_dummy/` (including `master.csv` and `features.csv`). C, A and H build against those while the humans rate, then switch to real files at G3 by dropping `--outputs outputs_dummy`. Fake numbers are **never** quoted.

## 4. Combining deliverables (so the merge takes minutes)
**Disjoint files.** Each person edits only their own files (CONTRACT §3), so there are no merge conflicts.

**Git (5 commands each time):**
```
git clone https://github.com/auctacius/utkarshpearl && cd utkarshpearl/safelabel        # once
git pull --rebase                           # always first
git add outputs/translations_zh.csv         # only YOUR files
git commit -m "zh translations"
git push
```
*Fallback if git is a hassle:* a shared Drive folder with the same layout; everyone uploads only their own files; H downloads and commits at G3.

**G3 merge (H, ~15 min):** pull → `python tools/tie_out.py --all --write --quiet` (must say `ALL CONTROL TOTALS TIE`) → tell C → C runs `python src/run_checks.py` → `python tools/tie_out.py --all --stage features --quiet` → tell A → A runs `python src/evaluate.py`. A `GAP:` line names the file and the missing/odd rows: message the owner with that exact line.

**Final repo:** `README.md` (write-up) · `PLAN.md` / `CONTRACT.md` (optional to keep) · `data/` · `src/` · `tests/` · `tools/` · `outputs/` (real CSVs, results, figures) · `app/` · `notebooks/SafeLabel_final.ipynb` · `requirements.txt`. Delete `outputs_dummy/`. Make the repo public, check the links in an incognito window.

**Final Colab notebook — the skeleton is already built:** `notebooks/SafeLabel_final.ipynb`. H fills the `<<...>>` parts and follows the checklist cell at its top. Every results cell reads the CSVs in `outputs/` and prints "(not available yet)" instead of crashing, so it can be run at any time (use `OUTPUTS_DIR = "outputs_dummy"` to rehearse on fake data). *Run all* must pass in a fresh runtime; save with outputs visible; no keys. Outline:
1. Title, one-sentence pitch, disclaimer *This project is a prototype and is not medical advice.*, how to run
2. Setup: `!git clone …`, `%cd safelabel`, `!pip -q install -r requirements.txt`
3. Data: the 60 sentences, categories, dev/test split
4. Human ratings: unsafe rate per language (table + chart), error types
5. Detectors vs baseline on the test split (table + chart + `TIE:` lines)
6. Failures: side-by-side English / machine / corrected (3 per language) and why we think each happened
7. chrF vs human verdict (Spearman per language)
8. Demo: `check_translation` + Gradio (with cached-examples fallback)
9. Limits, next steps, credits

## 5. Tokens and tools — spend them where they pay
| Person | Use the AI for | Don't spend tokens on |
|---|---|---|
| H | Claude: design review, integration, write-up polish. ChatGPT/Codex: bulk code (`app.py`, notebook cells). One cross-model review at G3. | re-explaining the plan; rating |
| C | Codex *in the repo folder* (so it reads `AGENTS.md` and runs the tests itself). Hardening `checks.py`, `run_checks.py`, LaBSE. | long chats; rating |
| A | Claude for `evaluate.py`, charts, findings, Results text. | rating; re-deriving the protocol (it is frozen in CONTRACT §5) |

Rules that save tokens:
1. Start each AI chat with `AGENTS.md` + `CONTRACT.md` + **your brief only** (about 4k tokens). Never paste this plan.
2. **Tests first.** Acceptance tests and `tie_out.py` already exist; paste only the failing output (last 30 lines).
3. Show data as header + 3 rows. Never paste a whole CSV.
4. One chat per work package; start a fresh chat when a chat gets long and put decisions in `NOTES.md`.
5. Ask for edits/diffs, not full rewrites. Use `--limit 5` smoke runs.
6. Use the strongest model for design and edge cases (once), a faster model for boilerplate.
7. Cross-check with the *other* model once per module (different models catch different bugs).
8. Ratings are human work; spending AI tokens to "explain" each sentence wastes time and weakens the study.

## 6. Risks and the cut line
| Risk | What we do |
|---|---|
| No Colab GPU / quota hit | CPU works for 60 short sentences (slower); a teammate with a GPU can run another language. |
| `translate.py` breaks (written without a GPU) | H fixes first (11:00–11:30) and tells everyone. |
| Very few unsafe rows (e.g. <8 per language) | Report counts, intervals and examples; say "this shows the error exists, not how often". Pool languages for detector results. |
| Rater uncertainty (heritage speakers, not certified translators) | Safety-first tie-break, `note` column, disclose in write-up; stretch S3 adds a second reader on 15 rows. |
| Translator writes numbers as words → number check false alarms | Report as a failure; stretch S4 adds target-side number words. |
| Script/dialect issues (Simplified vs Traditional, MSA vs spoken dialects, Hindi vs Hinglish) | State the choice in the write-up. |
| Over-claiming | The app never says "safe"; results are "on our 60 sentences"; disclaimer everywhere. |
| Tuning on test | Thresholds on dev only (CONTRACT §5). |
| Demo fails while recording | Record from the pre-run notebook; keep backup screenshots; cached-examples fallback. |
| The shared repo also holds other projects (`Adam's GPT` = PIIParity, `Alans Claude` = LocaleOS) | One project per team: agree today which one we submit. Link to the `safelabel/` folder, not the repo root. Never edit the other folders. |

**Cut line if time slips** (drop from the bottom): stretch goals S1–S5 → Gradio polish → per-category tables. **Never cut:** 3×60 human ratings, number+negation checks, the round-trip chrF baseline, the per-language table, 3 failure examples, a working demo on 6 cached examples, the write-up with the disclaimer.

## 7. Stretch goals (in value-per-minute order)
| # | Stretch | Owner | Time |
|---|---|---|---|
| S1 | LaBSE cosine as a stronger generic-quality baseline (makes the comparison fairer) | C | 45 min |
| S2 | Re-translate the NLLB-unsafe sentences with a Gemini model (free tier, your own key, never committed) and re-rate those rows: "does a stronger translator fix it?" Exploratory, labelled as such, `system = gemini` | any, after G3 | 60–90 min |
| S3 | Second reader (a relative or friend, with their permission, synthetic sentences only) rates 15 rows per language → agreement rate | each | 30 min |
| S4 | Target-side number words (两, एक, ثلاثة …) in `extract_numbers` | C | 60 min |
| S5 | Real chrF-vs-human check on 20 FLORES+ sentences (professional references exist there) | A | 60 min |

## 8. Demo video script (2:00 max — fill the `[ ]` after G4)
Structure from the official briefs: problem 15 s · demo 60 s · how it works 30 s · next steps 15 s. One narrator (H). Screen recording + voice-over is enough.

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:15 | Title card "SafeLabel", then an English label sentence | "Millions of families in the US read medicine labels in a second language, and many paste them into a free translator. But if 'every 8 hours' turns into 'every 6', or 'do not' disappears, that is not a typo. It is a safety risk." |
| 0:15–0:35 | App: paste `[sentence with a number error]`, choose Chinese. Red banner **Don't rely on this** + reason | "Here is a real example from our test. The free translator, NLLB-200, changed [number]. SafeLabel catches it and says: ask your pharmacist." *(Person C says the corrected sentence in Chinese — 3 seconds.)* |
| 0:35–0:55 | App: `[negation example]`, Arabic or Hindi. Banner + reason | "Here a 'do not' was lost in [language]. Same warning." *(Person A or H reads the correct sentence aloud.)* |
| 0:55–1:15 | App: a clean sentence → grey/green banner "No problems found by our checks — still confirm with your pharmacist". Then the side-by-side table (English / machine / corrected) | "When our checks find nothing, we still never say 'safe'. We say: confirm with your pharmacist." |
| 1:15–1:45 | Chart: unsafe rate per language; chart: detector recall | "We wrote 60 label-style sentences and translated them into Hindi, Chinese and Arabic. Each of us, a speaker of one language, rated every translation. [X]% of Hindi, [Y]% of Chinese and [Z]% of Arabic translations were unsafe. On held-out sentences, always saying 'fine' catches zero. A standard quality score, round-trip chrF, caught [A] of [N] unsafe ones. Our simple number and negation checks caught [B] of [N], with [C] false alarms per ten other sentences." |
| 1:45–2:00 | Limits slide | "Limits: only [n] test sentences per language, speakers rather than certified translators, and fluent-but-wrong errors slip through. Next: certified-translator review and more languages. This project is a prototype and is not medical advice." |

*Recording checklist:* pre-load the model and open the notebook before recording · browser zoom 125% · silence notifications · record each segment separately and join (no editing skills needed) · export MP4, upload to YouTube *unlisted* (or Drive "anyone with the link") · open the link in an incognito window · keep backup screenshots of every demo screen.

## 9. Write-up and submission checklist
- **Write-up:** `README.md` already follows the official template; fill the `<<…>>` parts (A drafts Results, each person adds their language note, H edits to one page). Must contain *This project is a prototype and is not medical advice.* and the **What we added** section.
- **Form needs:** track = **Languages** · every member's name, email, school (check spelling) · code link (the folder `https://github.com/auctacius/utkarshpearl/tree/main/safelabel`, or the Colab notebook shared as "anyone with the link" with outputs visible) · write-up link · video link · credits.
- **Credits (every dataset, model, tutorial and AI tool, with links):** NLLB-200 distilled 600M ([model page](https://huggingface.co/facebook/nllb-200-distilled-600M)) · [Hugging Face Transformers](https://github.com/huggingface/transformers) · [sacreBLEU](https://github.com/mjpost/sacrebleu) · [Gradio](https://www.gradio.app) · the AI tools each of you used (Claude, ChatGPT/Codex, Gemini if used) · related studies cited in the README (open each page and verify any number before quoting it).
- Open every link in a private window · submit v1 by **8:00 PM CT** · resubmit as you improve (the latest version counts).
- Optional pass: ask for a **mock judge score + finals Q&A prep** (the finals are Sat Nov 21, 11 AM ET: 5-minute talk + judge questions).

## 10. When you come back
Bring: the `GAP:`-free `tie_out` output, `outputs/results_*.csv`, `outputs/failures.csv` (top 6 rows), and the figure files. Then ask for any of:
1. final video script with the real numbers and your three best examples,
2. the final Colab notebook assembled and checked,
3. the README Results and "Where it fails" text,
4. a mock judge scoring (technical quality, impact, creativity, clarity + Languages-track extras) and finals Q&A prep.
