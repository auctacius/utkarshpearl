# SafeLabel — can you trust a machine translation of a medicine label?

> **TEAM: open `START_HERE.md` first. (H: delete this line and `START_HERE.md` before submitting.)**

**Track:** Languages
**Team:** <<names>> (Hindi: <<name>> · Chinese: <<name>> · Arabic: <<name>>)

> This project is a prototype and is not medical advice.

## The problem
Millions of people in the US read medicine instructions in a language that is not English, and many paste the label into a free translator. A changed number ("every 8 hours" → "every 6") or a lost "do not" can lead to a wrong dose. Earlier studies of machine-translated patient instructions found mostly good but sometimes dangerous errors, and results differ by language. <<Add 1–2 sentences with sources, e.g. the 2019 UCSF study of discharge instructions and the 2021 University of Arizona study of pharmacy directions — SOURCE: open the pages and verify every figure before quoting; otherwise write UNKNOWN>>

## What we built
**In:** one English medicine-label sentence and a language (Hindi, Chinese or Arabic). **Out:** the machine translation plus a verdict — *don't rely on this*, *unsure*, or *no problems found by our checks (still confirm with your pharmacist)* — with the reasons in plain language. **User moment:** a family member at the pharmacy counter who reads the translation instead of the English. The tool never says a translation is "safe".

## What we added
Started from the brief *Translation quality test* (NLLB-200). We added: **our own user** (medicine labels, a family member), **our own data** (60 synthetic label-style sentences with hand-checked number and negation labels), **our own question** (does a normal quality score catch dangerous errors, and do simple number/negation checks do better?), and **checks by real speakers** — each of us rated the translations in our own language.

## How it works
- **Data:** 60 synthetic sentences (drug names are made up), split 30 dev / 30 test by sentence. <<cleaning notes>>
- **Translator:** NLLB-200 distilled 600M (free). We also translate each result back to English.
- **Human rating:** `safe` / `minor` / `unsafe` + error type + a corrected translation for every unsafe one. Safety-first tie-break: if unsure, `unsafe`. Raters are heritage speakers, not certified translators. <<Simplified vs Traditional; MSA; second reader, if done>>
- **Detectors:** (1) *always safe* baseline; (2) round-trip chrF below a threshold chosen on dev only; (3) number check — do the same numbers appear on both sides; (4) negation check — do "do not / avoid / without" survive; (5) 3+4 combined, and combined with (2). <<LaBSE baseline, if done>>

## Results
<<A drafts this. Keep counts next to percentages and name which of H1/H2/H3 (CONTRACT.md) held.>>
- Unsafe translations (all 60 sentences): Hindi <<x/60>> · Chinese <<x/60>> · Arabic <<x/60>>. Most common error types: <<…>>
- On held-out test sentences (<<n unsafe of N>>): always-safe baseline recall **0**; round-trip chrF recall <<…>> / precision <<…>>; number+negation rules recall <<…>> / precision <<…>>; combined <<…>>; false alarms <<… per 10>>.
- **Where it fails:** <<3 side-by-side examples: English / machine output / correct translation, and why we think the checks missed or over-flagged them (e.g. fluent but wrong meaning; numbers spelled as words)>>

## What we'd do next
<<e.g. review by certified medical translators; more languages and spoken dialects; real label text from public-domain sources; a second human reader on every row>>

## Sources
- NLLB-200 distilled 600M — https://huggingface.co/facebook/nllb-200-distilled-600M
- Hugging Face Transformers — https://github.com/huggingface/transformers · sacreBLEU — https://github.com/mjpost/sacrebleu · Gradio — https://www.gradio.app
- Related studies — <<links, verified>>
- AI tools used: <<Claude, ChatGPT/Codex, Gemini (if used) — list what each was used for; ratings were made by humans only>>
