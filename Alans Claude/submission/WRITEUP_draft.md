# LocaleOS: know which translations to check

**Track:** AI + Languages
**Team:** [names]

> Draft. Every `[bracket]` is a number or fact that must come from our own Colab run
> (`data/results.json`). Do not submit with a bracket left in. Keep it to about one page.

## The problem
A small shop, school office or clinic that serves families in several languages cannot pay a
translator to check every line, so it pastes text into a free translator and publishes whatever
comes out. Most of it is fine. Some of it is wrong in ways that matter: a changed dose, a dropped
"not", a brand name mangled. The owner cannot read the result, so they cannot tell which lines
are the wrong ones.

## What we built
LocaleOS takes English text and returns translations in Spanish, Hindi, Mandarin, Arabic and
Kurmanji, each marked "looks fine", "worth a check" or "needs review", with the reason in plain
words and the translation turned back into English so a non-speaker can see what changed. The
owner sends only the flagged lines to a human.

## What we added
We started from suggested project 4.4.2 (Translation quality test) and added:
- **Our own user:** a small business deciding which translations to pay a human to check.
- **Our own question:** not "how good is the translator?" but "can we predict which
  translations are bad, without a human reference?" We also asked whether that works on a
  language the flagger never trained on.
- **Our own data:** 60 business strings we wrote (shop, app, clinic, school, notices), and
  ratings by native speakers on our team in all five languages.

## How it works
**Data.** FLORES+: the same sentences professionally translated into every language. We used
[N] sentences from the `dev` split to train and [N] from `devtest` to test, in five languages
([N] translations in each set). A translation is labelled bad when its chrF score against the
professional translation is in the lowest quarter for its language.

**Model.** NLLB-200 (a free pretrained translator) produces each translation. For every
translation we compute seven signals that need no reference: how much the meaning changes when
translated back into English, how far its meaning is from the source (LaBSE embeddings), the
translator's own confidence, missing numbers, odd length, repetition, and text left in English.
A logistic regression combines them into one review score. We chose logistic regression because
each weight is readable, which is how the app explains every flag.

## Results
If a human reviews only the 20% of translations LocaleOS flags, they see **[X]%** of the bad
ones. Baselines on the same held-out data: picking at random catches 20%; reviewing the longest
sentences first catches [Y]%; using the translator's confidence alone catches [Z]%.

| Language | Bad ones caught at 20% reviewed | Never trained on this language |
| --- | --- | --- |
| Spanish | [ ]% | [ ]% |
| Hindi | [ ]% | [ ]% |
| Mandarin | [ ]% | [ ]% |
| Arabic | [ ]% | [ ]% |
| Kurmanji | [ ]% | [ ]% |

Native speakers on our team rated [N] translations each, without seeing the flagger's score. The
flagger agreed with them on [ ]% and flagged [ ]% of the ones they called bad.

**Where it fails.** [One real example from the failure gallery: a bad translation it scored as
safe, and our best explanation. Likely candidates: a fluent sentence with the wrong meaning; an
idiom such as "break a leg" translated word for word; Kurmanji, where [what we observed].]
[Say plainly if the flagger barely beats translator confidence alone.]

## What we'd do next
- Have professional translators, not just our team, label a larger sample, since our "bad" label
  is automatic and compares wording with a single reference.
- Test with a real small business on its own website text.

## Sources
- FLORES+ dataset, Open Language Data Initiative: https://huggingface.co/datasets/openlanguagedata/flores_plus
- NLLB-200 translation model, Meta: https://huggingface.co/facebook/nllb-200-distilled-600M
- LaBSE sentence embeddings, Google: https://huggingface.co/sentence-transformers/LaBSE
- chrF metric via sacrebleu; scikit-learn; FastAPI
- Our own 60 business strings and native-speaker ratings
- AI tools: Claude (Anthropic) helped us plan, wrote first drafts of the code and this write-up's
  structure, and built the app's interface. We ran every experiment ourselves, checked every
  translation in our own languages, and can explain each part of the code. [Add any other tools.]

*This project is a prototype. Translations of medical, legal or safety text should always be
checked by a qualified person.*
