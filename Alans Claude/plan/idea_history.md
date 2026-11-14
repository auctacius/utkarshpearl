# Idea history: every round, in order

Alan's planning session with Claude, Saturday November 14, 2026. Scores are Claude's
judgement, not official numbers. "Risk-adjusted" = 30% Round 1 + 70% Finals (weights
from our prep note), minus 3 points for each Finishable point below 10.

## Round 1: AI + Finance, brief ideas plus six new ones

| Rank | Idea | Risk-adjusted |
| --- | --- | --- |
| 1 | FairDoor: mortgage approval odds with a fairness audit (HMDA data) | 76 |
| 2 | PumpGuard: crypto pump-and-dump warning (dataset verified, see experiments/pumpguard) | 76 |
| 3 | MainStreet Stress Test: small-business loan risk through 2008 (SBA data) | 70 |
| 4 | Scam text filter (brief 4.2.1) | 69 |
| 5 | ReliefRadar: will a CFPB complaint get money back | 63 |
| 6 | Fairness audit on German Credit (brief 4.2.3) | 62 |
| 7 | FundFair: microloan funding bias (Kiva) | 61 |
| 8 | FinePrint: costly clauses in payment-app terms | 61 |
| 9 | Card fraud detection (brief 4.2.2) | 56 |
| 10 | News headlines and the stock market (brief 4.2.4) | 51 |
| 11 | Bank-fee explainer | 50 |
| 12 | Teen budgeting assistant | 47 |
| 13 | City inflation tracker | 35 |
| 14 | Trading bot / stock predictor / auto-investor (team's first brainstorm) | 35 |

## Round 2: "genius" ideas

- **ScamBreaker**: attack the organisers' own sample scam filter. Tested: rewording fools it
  on 8 of 20 scams, look-alike characters on 14 of 20; the character model the sample
  dropped lets through only 3 and 0. See experiments/scambreaker. Team: "not it".
- AgentShield (AI bill-pay agents tricked into paying scammers), CloneCall (voice-clone scams).
- RideCheck (NYC gig-driver pay), HouseEdge (can AI beat the bookmaker), DarkCart
  (manipulative checkout text, 2,356 labelled snippets verified), ClosingTime (Yelp closures).

## Round 3: AI in finance itself

| Rank | Idea | Risk-adjusted |
| --- | --- | --- |
| 1 | AdvisorAudit: wrong or biased money advice from chatbots | 80 |
| 1 | LoanBot Bias Test: identical loan applications, different names | 80 |
| 3 | FilingCheck: wrong numbers in AI summaries of SEC filings | 75 |
| 4 | HerdWatch: does everyone get the same AI stock picks | 71 |
| 4 | AgentShield | 71 |
| 6 | ThinFile: alternative data for people with no credit history | 65 |
| 7 | FairWash: gamed explanations hiding bias | 61 |
| 7 | DeepfakeCFO | 61 |

Then: PoisonPill (planted pages make AI recommend a fake stock), B2B ideas TrueReason,
Canary ("would it have caught 2008?"), TwinBank, and kids' ideas BlindSpot and FutureSim.
Team decision: finance is oversaturated; switch tracks.

## Other tracks considered

SkinCheck Fairness (health), GrandmaASR and Lost in Translation (languages), FloodStreets and
SmokeDay (climate), LabLingo (health).

## Round 4: AI + Languages, chosen track

Team languages: Spanish, Kurmanji (Latin script), Mandarin, Hindi, Arabic.

| Rank | Idea | Risk-adjusted | Damn / 10 |
| --- | --- | --- | --- |
| 1 | The Language Tax | 82 | 9 |
| 2 | DoseSafe | 76 | 8 |
| 3 | GenderFlip | 76 | 7 |
| 4 | PhantomWords | 75 | 10 |
| 5 | CodeSwitch | 75 | 8 |
| 6 | LatinScript | 73 | 7 |
| 7 | NameGuard | 68 | 8 |
| 8 | GrandmaASR | 66 | 7 |
| 9 | EmergencyLine | 66 | 8 |
| 10 | ScoreCheck | 66 | 4 |
| 11 | LostIdioms | 65 | 6 |
| 12 | PoliteGap | 64 | 6 |
| 13 | CultureQuiz | 60 | 6 |
| 14 | SchoolNote | 55 | 5 |
| 15 | ModGap | 55 | 6 |

The Language Tax was then turned from a study into an app, **LinguaBridge**, covering all five
team languages. See demo/linguabridge.
