# Alan's Claude section

Work from Alan's sessions with Claude for the Veritas AI International High School Hackathon
2026 (submissions close Sunday, November 15, 11:59 PM ET).

## Our project: LocaleOS (AI + Languages track)

**LocaleOS helps a small business that can't afford to have every translation checked.** It
takes English text and gives back translations in Spanish, Hindi, Mandarin, Arabic and Kurmanji,
with the risky ones flagged for a human, and the reason why.

The AI at its centre is a **review flagger**: for each machine translation it computes seven
signals that need no human reference, and a logistic regression turns them into a review score.

### Status, honestly

| Part | State |
| --- | --- |
| Flagger code, dataset builder, evaluation, rating tools | Written; the whole pipeline ran end to end with **stand-in (fake) models** |
| The app (translate, flag, explain, export; evidence page) | Written; every state tested in a browser with stand-in models |
| Real translations, real training, real results | **Not run yet.** They need a GPU: run `LocaleOS_Colab.ipynb` |
| Write-up, video script, judge Q&A, Sunday runbook | Drafted in `submission/`, with `[brackets]` where our real numbers go |

The screenshots in `demo/localeos/screenshots/` are named `STANDIN_...` because they show fake
translations and fake results. Replace them after the Colab run, and never use them in the
write-up or video.

### Start here on Sunday
1. Read `submission/RUNBOOK.md` (roles, timeline, gates, checklist).
2. Open `demo/localeos/LocaleOS_Colab.ipynb` in Google Colab, set the runtime to T4 GPU, run the
   cells in order.
3. Each speaker rates their 30 translations (step 4 of the notebook).
4. Fill the brackets in `submission/WRITEUP_draft.md` and `submission/VIDEO_script.md`.

### Files in `demo/localeos/`
| File | What it does |
| --- | --- |
| `qe.py` | The seven signals and the flagger (logistic regression, saved as readable JSON) |
| `models.py` | The two pretrained models: NLLB-200 (translator) and LaBSE (sentence meaning) |
| `build_dataset.py` | Translates FLORES+ and our business strings; saves as it goes |
| `evaluate_qe.py` | Trains on `dev`, tests on `devtest`, baselines, per language, unseen-language test, failures |
| `ratings.py` | Makes blind rating sheets for native speakers and scores the flagger against them |
| `data/business_strings.json` | Our own 60 business texts |
| `server.py`, `web/` | The app |
| `standin.py` | Fake models, only for testing the code without a GPU |

To try the app without a GPU (fake models, clearly labelled on screen):

```bash
cd "Alans Claude/demo/localeos"
pip install fastapi uvicorn numpy scikit-learn sacrebleu
LOCALEOS_STANDIN=1 python build_dataset.py --n 300 && LOCALEOS_STANDIN=1 python evaluate_qe.py
LOCALEOS_STANDIN=1 python server.py
```

## Earlier work, kept for reference
| Folder | What it is |
| --- | --- |
| `demo/linguabridge/` | The earlier "language tax" app: what the same message costs in tokens per language. Its pilot ran on real tokenizers |
| `experiments/` | Language-tax pilot, ScamBreaker (attacking the sample scam filter), PumpGuard data check |
| `plan/` | The exported plan document and the history of every idea round |

## AI credits
Claude (Anthropic) helped plan, rank ideas, write the code in this folder and draft the
submission documents during the hackathon. The team runs every experiment, rates the
translations in their own languages, and must be able to explain every line before submitting.
