# Sunday runbook: from code to submission

Submissions close **Sunday, November 15 at 11:59 PM ET**. No late submissions. All times ET.

## Roles
| Role | Owns |
| --- | --- |
| Builder | The Colab runs: translate, train, test. Explains the model in the video and Q&A |
| Integrator | The app running in Colab, the demo path, recording the demo segment |
| Storyteller | Ratings from all five speakers, the failure example, write-up, video, submission form |

## Timeline and gates
| When | Do | Gate: stop and decide if not met |
| --- | --- | --- |
| 9:00 AM | Builder: open `LocaleOS_Colab.ipynb`, T4 GPU, run steps 1 and 2 | **10:00 AM:** FLORES+ has loaded and the first language is saved. If not, see "If FLORES+ will not load" |
| 10:00 AM | Builder: step 3 (train and test). Storyteller: step 4, send each speaker their ratings file | **1:00 PM:** the baselines table exists and has been read aloud to the team |
| 10:30 AM | Everyone: rate your 30 translations (about 20 minutes each) | |
| 1:00 PM | Builder: `ratings.py score`; commit `model.json`, `results.json`, ratings to GitHub. Integrator: launch the app (step 6), rehearse the demo path. Storyteller: pick the failure example | **3:00 PM, feature freeze.** After this: fixes, evidence and presentation only |
| 3:00 PM | Storyteller: fill every bracket in the write-up and the video script. Record a rough backup video | |
| 4:00 PM | Explain-back drill: each person explains one file they did not run. Delete or simplify anything nobody can explain | |
| 5:00 PM | Record the final video in four takes. Upload as Unlisted | **6:00 PM:** first submission sent, even if rough |
| 6:00 PM | Open every link in a private window. Fix only what is broken | **10:00 PM:** final submission sent |

## Submission checklist
- [ ] Code: the GitHub repository, public, with the notebook saved **with its outputs visible**
- [ ] Write-up: about one page, no brackets left, in the template's headings
- [ ] Demo video: under 2:00, Unlisted on YouTube or Drive with link sharing
- [ ] Team details: track AI + Languages; every name, email and school spelled correctly
- [ ] Credits: every dataset, model, library and AI tool, with links
- [ ] Every link opens in a private window
- [ ] No stand-in screenshots or numbers anywhere

## Form answers (draft)
| Question | Answer |
| --- | --- |
| Project title | LocaleOS: know which translations to check |
| Track | AI + Languages |
| Starting point | 4.4.2 Translation quality test |
| One-sentence pitch | LocaleOS helps a small business that can't afford to have every translation checked, by taking its English text and giving back translations in five languages with the risky ones flagged for a human, and the reason why. |
| What we added | Our own user (a small business), our own question (can we predict which translations are bad without a reference, even for a language the flagger never trained on?), and our own data (60 business strings plus native-speaker ratings in five languages). |
| Datasets, models and AI tools | FLORES+; NLLB-200; LaBSE; sacrebleu; scikit-learn; FastAPI; Claude for planning, code drafts and the interface |

## If FLORES+ will not load
1. Check you accepted the terms on the dataset page and ran the login cell with a token that has
   read access.
2. `build_dataset.py` already tries the older `facebook/flores` copy automatically.
3. If Mandarin alone fails, run the other four: `python build_dataset.py --languages Spanish Hindi Arabic Kurmanji`.
4. Last resort: run only `--business` and report native-speaker ratings as the main evidence,
   saying plainly that there is no held-out FLORES+ test.

## If results disappoint
Report them. "The flagger adds little beyond the translator's own confidence" or "it does not
transfer to Kurmanji" is an honest finding, and the brief says an honest modest result scores
above an unexplained high one.

## Cut order if time runs out
Drop first: protected terms, the export button, the never-trained-on-this-language test.
Never drop: baselines, the held-out test, native-speaker ratings, the failure example, the write-up.
