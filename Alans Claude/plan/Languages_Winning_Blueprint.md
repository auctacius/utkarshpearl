# Veritas AI Hackathon 2026: AI + Languages Winning Blueprint

Nov 14, 2026 · @alan

## Bottom line

We are switching to the Languages track, and **The Language Tax** ranks first of 15 ideas at 82. **PhantomWords** has the highest Damn factor, 10 of 10, but is harder to finish.

Three speakers of three languages is the team's edge. Every experiment runs in three languages, and each of us is the native-speaker check the brief asks for.

**Before the 1 PM meeting.**

- [ ] Write down our three languages. A less-served language makes every finding stronger.
- [ ] In Colab, check that FLORES+ loads from Hugging Face. It needs a free account and accepted terms.
- [ ] Vote between The Language Tax and PhantomWords, or bring a third from the list.

### What Kurdish, Mandarin and Hindi change

Our three languages form a ladder: Mandarin is well served by AI, Hindi is in the middle, and Kurdish is badly served. That makes The Language Tax stronger, because we can show the cost and the errors rising step by step as support falls.

| Idea | Effect of our languages |
| --- | --- |
| The Language Tax | Stronger. Three rungs plus English give a curve, not one comparison. Kurdish is the headline |
| DoseSafe | Stronger. Kurdish translation is likely the weakest, and a Kurdish speaker can judge it |
| LatinScript | Stronger. Hindi is often typed in English letters, Mandarin has pinyin, and Kurdish is written in two scripts |
| CodeSwitch | Strong for Hindi mixed with English; less natural for the other two |
| GenderFlip | Partial. Kurdish and spoken Mandarin use one word for "he" and "she"; Hindi verbs mark gender, so it fits less well |
| PhantomWords and GrandmaASR | Weaker for Kurdish. From memory, Whisper does not support Kurdish at all; check its language list. That absence could itself be a finding |

Our Kurdish is Kurmanji, written in Latin script. From memory, its code in FLORES+ and the NLLB translation model is `kmr_Latn`, Hindi is `hin_Deva` and Mandarin is `zho_Hans`; confirm all three load in Colab. Two Kurmanji details to test:

- **Missing accents.** People often type Kurmanji without its special letters (ç, ê, î, ş, û). For Kurmanji, the LatinScript idea becomes: does AI still cope when the accents are dropped?
- **Mistaken identity.** Language detectors may confuse Kurmanji with Turkish, because they share letters. That is a small, checkable finding to add to The Language Tax.
- **Gender.** Kurmanji's "ew" means both "he" and "she" in simple sentences such as "Ew bijîşk e", so GenderFlip works for it; our speaker should confirm the test sentences.

## The Language Tax, upgraded

A pilot run this morning found the headline: newer AI models cut Hindi's token tax from 4.4 times English to 1.4 times, but Kurmanji's stayed near 2 times on every model generation.

AI models read text in pieces called tokens, and they charge, slow down and run out of memory by the token. A language that needs twice the tokens pays twice the price and fits half as much into the model's memory.

&#91;embedded content: Pilot, Saturday morning · 12 sentences translated by Claude, not yet checked by our speakers · 4 tokenizers shipped in Meta's and Mistral's Python packages\]

Mandarin costs about the same as English. Dropping Kurmanji's accented letters cuts its tokens by 13 to 16%, so the tokenizer charges extra for the language's own alphabet.

### The demo moment

One word, four languages, on Llama 4's tokenizer:

| English | Hindi | Mandarin | Kurmanji |
| --- | --- | --- | --- |
| doctor: 1 token | डॉक्टर: 1 token | 医生: 2 tokens | bijîşk: 3 tokens ("bij", "î", "şk") |
| medicine: 1 token | दवा: 2 tokens | 药: 1 token | dermanê: 3 tokens |
| library: 1 token | पुस्तकालय: 4 tokens | 图书馆: 3 tokens | pirtûkxane: 5 tokens |

The accented letters î and û become tokens of their own. That is the tax, visible in one word.

### What the pilot does not prove yet

- It is 12 sentences that I translated; our speakers must check them, and the real run uses 1,012 professionally translated FLORES+ sentences.
- Four tokenizers, two companies. GPT and Gemini tokenizers load in Colab but were blocked from my session.
- Token cost is only half the story. Whether answers get worse is the second half, and it is untested.

### The project in four layers

1. **The tax map.** Run the same 1,012 FLORES+ sentences through six or more tokenizers in all of its 200-plus languages. Place Kurmanji, Hindi and Mandarin on a chart of every language: tax against number of speakers. Free, CPU only, done by Saturday night.
2. **The time machine.** Order tokenizers from GPT-2 (2019) to Llama 4 (2025) and ask which languages AI fixed and which it left behind. The pilot already shows Hindi fixed and Kurmanji not.
3. **Does the tax cost answers?** Score an open model in Colab on the Belebele reading test, which uses the same passages in over 100 languages; I believe Kurmanji, Hindi and Mandarin are all included, but check. Each of us rates 20 answers in our own language. English is the baseline.
4. **The fix.** Train a small Kurmanji vocabulary extension on Kurmanji text, then measure the tax on sentences it never saw. Be honest about the limit: a model must be retrained to use new tokens, so this measures how much of the gap a model maker could close.

### Demo: the Language Tax Calculator

A Gradio page. Paste text in any language and see tokens per model, the cost multiple against English, how much of the model's memory it uses, and the word-by-word token splits. A toggle switches between model years to show the time machine.

**Video line.** "Ask an AI something in Kurmanji and you pay about double. Hindi's price fell by two-thirds in two years; Kurmanji's hasn't moved."

### How it scores

- **Baseline:** English, and the oldest tokenizer.
- **Held-out test:** the fix is trained on FLORES+ dev sentences and measured on devtest sentences.
- **Per-language results and real speakers:** three languages, each checked by its own speaker, which is exactly what the Languages brief asks for.
- **Side-by-side examples:** the word splits above.
- **Honesty:** the accent finding and the retraining limit are stated, not hidden.

### From the 1 PM meeting to Saturday night

| Who | 1 to 6 PM | 6 to 10 PM |
| --- | --- | --- |
| Builder | Load FLORES+ and six tokenizers; run the tax map | Time machine across tokenizer years |
| Integrator | Calculator page with token splits | Wire in the map and the year toggle |
| Storyteller | Check our 12 pilot sentences; set up Belebele | First accuracy numbers per language |

The three of us each verify our own language's sentences and rated answers. That is the native-speaker check judges look for.

## The 15 language ideas

Each idea is a measurable question about how AI treats our languages, with our own speakers as the judges.

| Idea | The question | Data | Simple baseline |
| --- | --- | --- | --- |
| **The Language Tax** | Does the same question cost more and get a worse answer in our languages than in English? | FLORES+ parallel sentences; tokenizers of several AI models; a question set we translate | English cost and accuracy |
| **PhantomWords** | Does speech AI invent sentences nobody said, and more often in our languages? | Silence, noise and short clips we record; Whisper | English clips; an empty transcript |
| **DoseSafe** | When AI translates a medicine label, how often does it change the dose, timing or warning? | About 100 label instructions we write from public templates; NLLB | English back-translation check |
| **CodeSwitch** | Does AI break when we mix our language with English mid-sentence? | 100 to 150 real mixed sentences from each of us | The same content in one language |
| **GenderFlip** | Translating from a language with no "he" or "she", does AI guess doctors are men and nurses are women? | Job sentences we write in our languages | A 50/50 split |
| **LatinScript** | Does AI fail when our language is typed in English letters, the way we actually text? | Our own romanised messages; language detectors and translators | The same text in native script |
| **NameGuard** | Does AI mangle names from our cultures in speech and translation? | Lists of common names, recorded by us | Common English names |
| **GrandmaASR** | Does speech AI understand older speakers of our languages? | Common Voice age labels; family recordings with permission | Young adult speakers |
| **EmergencyLine** | Would speech AI understand an emergency call in our languages or accents? | Emergency phrases we script and record | Unaccented English |
| **ScoreCheck** | Do automatic translation scores agree with what native speakers think? | 100 translations per language, rated by us | The chrF score alone |
| **LostIdioms** | Does AI translate our proverbs by meaning or word for word? | 50 idioms per language, with meanings we write | Literal translation |
| **PoliteGap** | Does translation keep the respect levels our languages use for elders? | Sentences at formal and casual levels | The correct level, per speaker |
| **CultureQuiz** | Does AI know our festivals, food and history, and better in English than in our language? | A quiz we write in both languages | English score |
| **ModGap** | Does AI moderation miss bullying written in our languages? | Public hate-speech sets where they exist | English detection rate |
| **SchoolNote** | Can AI rewrite school notices so immigrant parents understand them? | Public school notices; parent ratings | Raw machine translation |

## Ranking with the rubric and the Damn factor

Rubric scores use your prep note's weights: 30% Round 1 plus 70% Finals, then 3 points off for each Finishable point below 10. The Damn factor is separate, from 1 to 10: how hard the headline hits someone hearing it for the first time. All scores are my judgement.

| Rank | Idea | Round 1 / 100 | Finals / 100 | Weighted / 100 | Finishable / 10 | Risk-adjusted | Damn / 10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **The Language Tax** | 88 | 83 | 85 | 9 | **82** | 9 |
| 2 | **DoseSafe** | 86 | 81 | 82 | 8 | **76** | 8 |
| 3 | **GenderFlip** | 78 | 80 | 79 | 9 | **76** | 7 |
| 4 | **PhantomWords** | 85 | 84 | 84 | 7 | **75** | **10** |
| 5 | CodeSwitch | 82 | 80 | 81 | 8 | 75 | 8 |
| 6 | LatinScript | 78 | 75 | 76 | 9 | 73 | 7 |
| 7 | NameGuard | 75 | 73 | 74 | 8 | 68 | 8 |
| 8 | GrandmaASR | 78 | 78 | 78 | 6 | 66 | 7 |
| 9 | EmergencyLine | 78 | 78 | 78 | 6 | 66 | 8 |
| 10 | ScoreCheck | 72 | 67 | 68 | 9 | 66 | 4 |
| 11 | LostIdioms | 67 | 68 | 68 | 9 | 65 | 6 |
| 12 | PoliteGap | 72 | 70 | 70 | 8 | 64 | 6 |
| 13 | CultureQuiz | 70 | 65 | 66 | 8 | 60 | 6 |
| 14 | SchoolNote | 66 | 64 | 64 | 7 | 55 | 5 |
| 15 | ModGap | 72 | 69 | 70 | 5 | 55 | 6 |

### The top four

**1. The Language Tax.** The headline is "AI charges you more for a worse answer when you don't speak English." Part one counts tokens for the same sentences in each language, needs no GPU or key, and gives a finding by Saturday evening. Part two measures answer accuracy per language. Part three tests a fix: translate to English, ask, translate back. Researchers have reported tokenizer gaps between languages; our addition is our three languages, the accuracy half and the fix.

**2. DoseSafe.** It has the clearest harm: a wrong number on a medicine label. We count only critical errors (dose, timing, dropped warning), judged by native speakers, then test a fix that locks numbers before translating. It needs the line "This project is a prototype and is not medical advice."

**3. GenderFlip.** It is the easiest to finish and demos in one sentence. It ranks below the top two on originality, because the effect is well known in a few languages. It only works if one of our languages has gender-neutral pronouns.

**4. PhantomWords.** It has the best ten-second demo: play silence, and the AI writes a sentence. Researchers have reported that Whisper sometimes invents text; the open question is whether it does so more in our languages. It ranks fourth only on finish risk: it needs audio handling on a GPU, and the rate may turn out low.

### My recommendation

Build The Language Tax. If the team wants the bigger wow and one of us has handled audio before, build PhantomWords. Do not combine them; the playbook's scope rule applies.

The roles, weekend rules, video steps and submission checklist below still apply. The sections written for the finance ideas were removed and will be rebuilt for whichever idea wins at 1 PM. The sample submission notes stay, because the organisers' sample is still the scoring template.

## What the judges score

The kickoff brief lists four criteria with no weights. Your prep note records point weights that put 70% of the final score on the live finals. I could not open the hackathon site to confirm them, so the plan is built to score under both.

| Criterion | What judges look for | How we show it |
| --- | --- | --- |
| Technical quality | It works, the approach is sound, it was tested fairly | Baseline beside the model, a later-year test set the model never saw, a gallery of failures |
| Impact | A real problem for real people | One named user, one moment they reach for the tool, what changes for them |
| Creativity | A fresh approach, not a repeated tutorial | Our own data, our own setting, our own question |
| Clarity | A judge understands it in two minutes | One takeaway sentence, a demo that runs start to finish, a one-page write-up |

### Point weights from your prep note

Final score = 30% Round 1 + 70% Finals.

| Round 1, blind review | Points | Finals, live demo | Points |
| --- | --- | --- | --- |
| Technical execution | 30 | Demo and clarity | 30 |
| Originality | 20 | Technical depth | 30 |
| Impact and track fit | 20 | Impact | 20 |
| Testing and honesty | 15 | Q&A | 20 |
| Communication | 15 |  |  |

- Round 1 is the gate: only finalists reach the 70%. The project has to read well on paper first, then demo well live.
- Demo and Q&A are half the finals score. A live moment that lands in ten seconds, and rehearsed answers, are worth more than extra tuning.
- Testing and honesty is 15 points your note says most teams skip: a baseline, a held-out test set and stated failures.
- Finalists are questioned live, so we build only what all three of us can explain line by line.

**Languages track tie-breakers.** Judges pay extra attention to three things, from the brief:

- Real examples shown side by side: what the model produced and what it should have produced.
- Results broken down by language or accent, never one overall average.
- Checks by a real speaker of the language. With three languages on the team, we have three.
- The track also requires public datasets or our own voices and writing. Recording anyone else needs their permission.

**Four questions every project must answer.** Who is it for? What goes in and what comes out? Does it beat a simple baseline? Where does it fail? All results must come from test data the model never saw, and dated data must be split by time.

**How the two rounds work.**

1. Round 1 is a blind review by the Veritas AI team. Reviewers see the project, not names or schools.
2. Finalists are emailed on Wednesday, November 18.
3. Finals are live on Saturday, November 21 at 11:00 AM ET: five minutes to present, then questions from a panel of AI researchers.

**What this means for us.**

- An honest, modest result outscores an unexplained high one. The brief says this twice.
- Suggested projects are compared with each other and scored on what the team added. Following the steps exactly lands at the low end.
- AI must do the main job. A website built with AI coding tools does not count on its own.
- If we call an AI API, judges score what we built around it: data, evaluation and interface.
- Nothing on the rubric rewards a startup look, a backend or a pitch deck. Clarity and honest testing are what score.

**Prizes.** The Gold team wins a remote AI internship; your prep note names Arecibo AI, a healthcare AI startup. Other awards are scholarships up to 100% for Veritas AI programs, Best Beginner Build, Best AI for Good, Judges' Choice and Merit Awards.

## What the sample submission teaches us

ScamCheck is the organisers' own model of a good submission, so its structure is the scoring template and its admitted gaps are our openings. It uses only scikit-learn and 40 hand-written test messages, which shows that honest testing scores, not model size.

| What ScamCheck does | Why it scores | How we go further |
| --- | --- | --- |
| Names one user: grandparents | Answers "who is it for" | Name one user and one moment, then test with two or three real people |
| Starts with a baseline: 86.6% accuracy, 0% recall | Shows why accuracy misleads | Two baselines: the majority class and a human rule of thumb |
| Writes its own 40-message modern test set | "Your own data"; exposes that Model 1 catches 3 of 20 | Real records at hundreds of times the scale, split by year |
| Makes one improvement from its error analysis: 3 of 20 becomes 16 of 20 | Explains the reasoning behind a change | An improvement driven by a fairness audit, with its accuracy cost |
| Tries character n-grams, drops them, says why | Honest about what did not work | Keep a "tried and dropped" log from hour one |
| Explains each warning with its top words | Builds trust | Explain in the user's terms and show what a score means |
| Admits it picked the model using the test set | Honesty about limits | Lock the test year and open it once, at the end |

**Gaps we can exploit.**

- The modern test set is 40 messages written by the authors. A 16 of 20 result has wide uncertainty and no confidence interval.
- The model was chosen on the test set, which the sample admits.
- The split is random, though the sample's own finding is that scams change over time.
- The threshold is fixed at 0.5, with no cost-based choice and no check of what "58%" means.
- Explanations surface tokens such as "99" and "held", which do not help a grandparent.
- There is no subgroup check: which scam types, or which users, it fails for.
- There is no demo video, no hosted demo and no real-user test. The sample lists the user test as a next step.

## Team roles and the weekend plan

A working demo by Saturday 10:00 PM ET is the plan's one hard target. It leaves all of Sunday for evidence, the write-up and the video.

&#91;embedded content: Weekend roadmap · 5 phases, 5 gates, times in ET\]

Each gate is a pass-or-switch point. The roadmap was drawn before the switch to Languages; its Sunday times and gates still hold, and Saturday now starts from the 1 PM meeting.

### Three roles

Your vault note already splits the team into ML and data, demo UI, and write-up plus video plus testing. The plan uses that split, not the Gemini prompt's backend role, because there is no backend to build. Your playbook says the storyteller role wins hackathons. Under these weights it owns the most points: communication, testing and honesty, and Q&A preparation.

| Role | Owns | Hands over |
| --- | --- | --- |
| Builder (ML and data) | Loading and cleaning the data, the year split, baselines, models and the one improvement | Baseline numbers by Saturday 1 PM; a model that beats them by Saturday 6 PM |
| Integrator (demo UI) | The Gradio demo, wiring the model into it, and a notebook that runs top to bottom | An ugly input-to-output demo by Saturday 1 PM; the real model in it by Saturday 10 PM |
| Storyteller (testing, write-up, video) | The evidence: test results, failure cases and audit tables; plus the write-up, video, AI log and submission | A results table by Sunday noon; first submission by Sunday 6 PM |

Everyone reviews one other person's section and can explain every cell aloud. The rules require that the whole team understands every part of the project.

### Rules of the weekend

- Feature freeze at Sunday noon ET, your playbook's 75% mark. After that: bug fixes, evidence and presentation only.
- Build the demo path first: the exact clicks the video will show.
- Commit every working state to GitHub, with a message such as "works: model + UI".
- Keep a running "tried and dropped" log. It becomes half the write-up.
- Cap any argument at 15 minutes, then pick one and move on.
- If you are stuck on one bug for 30 minutes, simplify or swap in a teammate.

## Tools, accounts and API keys

A Languages project needs no paid service. Text ideas run on a free Colab CPU; speech ideas need Colab's free GPU. Only the optional extras need keys.

| Tool | What we use it for | Key or account | Cost and limits |
| --- | --- | --- | --- |
| Google Colab | The one shared notebook, and the code we submit | Google account | Free; free GPU time is limited, so save results as you go |
| GitHub | Version history and a backup home for the write-up | Account; your linked repo is empty and ready | Free |
| Hugging Face | Datasets (FLORES+, Common Voice, FLEURS) and models (Whisper, NLLB, tokenizers) | Free account; some datasets ask you to accept terms | Free |
| Gradio | The demo | None | Free; `share=True` gives a temporary public link, [reported](https://www.gradio.app/3.50.2/guides/sharing-your-app) to last 72 hours |
| Gemini API (optional) | One commercial model to compare against the open ones | Key from Google AI Studio | Free tier; [recent reports](https://www.aifreeapi.com/en/posts/google-gemini-api-free-tier) say 20 requests a day on Flash models and 500 on Flash-Lite |
| QuickTime, OBS Studio or Loom | Screen recording | Loom needs an account | OBS is free; Loom's free plan is [reported](https://dupple.com/learn/is-loom-free) to cap at 5 minutes a video |
| YouTube | Hosting the video as unlisted | Google account | Free |

The Gemini and Hugging Face limits above come from third-party reports I could not confirm. Check your own project's limits page in AI Studio and try creating one Space before relying on either.

### Key safety

- Never paste a key into a notebook cell, a commit or the write-up. Judges open the notebook with its outputs visible.
- In Colab, store keys under the key icon (Secrets) and read them in code. Secrets stay with your account and are not shared with viewers.
- On a hosted demo, store the key as an app secret, not in the code.
- Add `.env` and `kaggle.json` to `.gitignore` before the first commit.
- If a key leaks, revoke it and create a new one. It takes a minute.
- The notebook must "Run all" with no keys. Put any API step behind a switch that is off by default, as the sample does with `RUN_APP = False`, and save example outputs.
- Send no personal data to any API. Demo inputs are made-up applicants.

```python
from google.colab import userdata

GEMINI_API_KEY = userdata.get("GEMINI_API_KEY")
```

### Setup checklist

- [ ] One shared Colab notebook with edit access for all three
- [ ] GitHub repo with a README started from the write-up template
- [ ] A cell that runs `pip install fairlearn gradio` without errors
- [ ] Screen recorder tested with a microphone
- [ ] Optional: Gemini key created and stored in Colab Secrets
- [ ] Optional: Hugging Face account, and one test Gradio Space created

## Generative AI: where it helps and where it stays out

The rules allow coding assistants and chatbots as long as the team understands every part and lists every tool. We use generative AI for planning, coding help and one optional feature, and keep it out of the results.

| Use | Verdict | Our rule |
| --- | --- | --- |
| Planning and brainstorming, including this document, which was drafted with Claude | Yes | List it in the write-up and on the form |
| Coding help: debugging, explaining and routine code | Yes | A human reads every line; whoever pastes it explains it aloud to a teammate |
| Explaining concepts such as calibration | Yes | Then confirm in the scikit-learn or Fairlearn docs, as the sample team did |
| Inside the product: an AI model we test or build on | Optional | Judges score what we add around it: our data, our testing and who it is for |
| Producing results or numbers | No | Every number in the write-up traces to a notebook cell |
| Writing the whole write-up | No | We draft it; AI may tighten the wording |
| AI voice or avatar in the video | No | Our own voices; judges are checking that we understand the work |

### The AI log

Keep a five-column note from hour one: time, tool, what we asked, what we kept, who checked it. It becomes the "AI tools used" answer on the form. It also prepares us for the question "which parts did AI write?"

### Explain-back drill

On Sunday at 4:00 PM ET, each member explains one section they did not write. If nobody can explain a cell, simplify it or delete it.

## Demo video plan

The video is optional but recommended and capped at two minutes. Ours is a 1:55 screen recording with our own voices that follows the brief's four-part structure.

| Part | Time | On screen | Who speaks |
| --- | --- | --- | --- |
| The problem | 0:00 to 0:15 | Title card with the one-sentence pitch and the headline number | Storyteller |
| The demo | 0:15 to 1:15 | One real input in each of our languages, with the model's output beside the correct one | Integrator, with each of us reading our own language |
| How it works | 1:15 to 1:45 | The results table, one row per language, baseline beside model | Builder |
| Limits and next steps | 1:45 to 1:55 | One limits slide | Storyteller |

### Production steps

1. Record a rough backup at Sunday noon ET, your playbook's hour 36. If everything later goes wrong, this is the video.
2. Write the final script word for word between noon and 2:00 PM ET, once the numbers are final.
3. Rehearse once against a timer.
4. Set the screen: 1080p, browser zoom at 125% to 150%, bookmarks and notifications hidden, inputs pre-filled.
5. Record four takes, one per part, with QuickTime, OBS Studio or Loom. Clear audio matters more than picture quality.
6. Join the takes with hard cuts in iMovie, CapCut or any free editor, and cut every second of loading.
7. Turn on captions and read them once for errors.
8. Export as MP4 under 2:00.
9. Upload to YouTube as Unlisted, not Private, or to Google Drive with "anyone with the link can view".
10. Open the link in a private window, and keep the MP4 in Drive as a backup.

### What sinks a demo video

- Running past 2:00.
- A private link the judges cannot open.
- Text too small to read.
- Narrating code instead of showing an input going in and a result coming out.
- Leaving out the baseline number.

Round 1 is a blind review, so keep faces, names and the school out of the video. The form carries the team details.

### If we reach the finals

Finalists present for five minutes on November 21, then take questions. Your note puts 70% of the final score here. Use the same structure with more time on the demo and results, and start with the problem, not the tech stack. Run the demo live, with this recording open as a backup. Rehearse at least five times aloud with a timer, and have every teammate speak.

## Submission checklist

A submission counts once the form holds working links to the code and the write-up. Ours goes in first by Sunday 6:00 PM ET and is replaced by the final version by 10:00 PM, two hours before the 11:59 PM deadline.

- [ ] **Code.** A Colab notebook or GitHub repo that anyone with the link can view, saved with outputs visible, and "Run all" works with no keys.
- [ ] **Write-up.** About one page, using the template's seven headings: The problem, What we built, What we added, How it works, Results, What we'd do next, Sources.
- [ ] **Disclaimer.** Required only for health or finance projects. If we build DoseSafe, add "This project is a prototype and is not medical advice."
- [ ] **Results.** The baseline score beside the model score on the held-out year, plus at least one failure with our guess why.
- [ ] **Demo video.** Two minutes or less, on YouTube as unlisted or on Drive with link sharing.
- [ ] **Team details.** Track AI + Languages, and every member's name, email and school spelled correctly.
- [ ] **Credits.** Every dataset, pretrained model, library, tutorial and AI tool, with links.
- [ ] **Link test.** Every link opened in a private window.
- [ ] **First submission** sent by Sunday 6:00 PM ET.
- [ ] **Final submission** sent by Sunday 10:00 PM ET.

If the upload fails at the deadline, email contact@veritasai.com at once with the code and write-up links. One person submits for the whole team.

Put a screenshot of the demo at the top of the write-up. Your playbook notes that many judges read only the first screen.

## Sources and datasets

This session could open GitHub but not most other sites, so the sources fall into two groups. Open each link in the second group before relying on it.

### Read directly

- The Project Briefs, Hacker Guide and ScamCheck sample submission you attached. The Languages brief names FLORES+, NLLB-200, Common Voice, FLEURS, Whisper and Tatoeba.
- Your two vault notes, "Hackathon Prep" and "How to Win Hackathons", for the point weights, role split and checkpoints.

### Found by search, not opened

- Gemini free-tier reports from [aifreeapi.com](https://www.aifreeapi.com/en/posts/google-gemini-api-free-tier) and [imisofts.com](https://imisofts.com/blog/gemini-api-free-tier-limits/).
- [Gradio sharing guide](https://www.gradio.app/3.50.2/guides/sharing-your-app) and [Loom's free plan](https://dupple.com/learn/is-loom-free).
- [Veritas AI's own post on winning hackathon projects](https://www.veritasai.com/veritasaiblog/best-hackathon-project-ideas-for-high-school-students-that-actually-win), which says judges look for "a real and specific problem, a technically sound approach, and evidence that the team understood the tradeoffs".
- The research behind the Language Tax and PhantomWords ideas is cited from memory. Hugging Face is blocked from this session, so none of the language datasets was load-tested here.
