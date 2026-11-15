# Model and inference contract
Selected: [urchade/gliner_multi-v2.1](https://huggingface.co/urchade/gliner_multi-v2.1), exact revision `443d26d654e0324125a96bebd8e796c14ff2efe6`. Model card declares **Apache-2.0**. Authors: Urchade Zaratiana, Nadi Tomeh, Pierre Holat, Thierry Charnois. Paper: https://arxiv.org/abs/2311.08526 . Weights are downloaded separately and not redistributed in this repository.

The underlying tokenizer/config is [microsoft/mdeberta-v3-base](https://huggingface.co/microsoft/mdeberta-v3-base), revision `a0484667b22365f84929a935b5e50a51f71f159d`; its card declares MIT. No base-model weights are downloaded. Asset sizes and SHA256 hashes are in reports/model_assets.json. The GLiNER safetensors file is about 1.16 GB. Allow several GB for the environment and model RAM.

We also examined Davlan/bert-base-multilingual-cased-ner-hrl: its card lists AFL-3.0 and PER/LOC/ORG training in ten languages; it does not cover the full requested label/language set. GLiNER's requested-type predictions and Apache license were a more direct fit. We did not execute Davlan.

## Fixed settings and adaptations
CPU, four Torch threads, evaluation/inference mode, strict state loading, safetensors only; GLiNER 0.2.22, Transformers 4.51.0, Torch 2.7.1. Requested labels, in fixed order: person, location, email address, phone number. Map these to PERSON, LOCATION, EMAIL, PHONE. Threshold 0.5; flat entities. Scores are model ranking outputs, not calibrated probabilities or safety guarantees. This configuration was not optimized against a held-out set.

Original text is never normalized or translated. The default GLiNER word splitter separated Hindi combining marks and treated long Han runs as one word. Our splitter groups Unicode letters with marks and exposes each Han character as a word unit. Every unit retains original code-point offsets; every model span is checked against its returned original substring. This preprocessing is part of our system, not a claim about unmodified GLiNER performance. The model still has a maximum span width of 12 word units.

Limits: reject inputs above 1,500 characters, 300 word units or 320 pretokenized subword tokens, reserving model capacity for labels. No silent truncation or partial-result fallback. Transformer fast-tokenizer byte-fallback warning remains; rare characters can become unknown tokens. All selected and rejected-overlap counts are exposed in the programmatic result.

## Language evidence and failures
All six languages executed locally, but no target language has validated independent accuracy. Broad multilingual pretraining is not proof of dependable coverage.

| Language | Actual fictional demo result / limitation |
| --- | --- |
| English | Detected Mira Patel, London and phone. AI missed email; hybrid covered it. |
| Hindi | After splitter correction, detected full name and Delhi. Small development fixture errors remain. |
| Simplified Chinese | After splitter correction, detected name and Beijing. AI missed email; hybrid covered it. |
| Spanish | Detected full name, Madrid and email in demo. |
| Turkish | Detected name; location span also included the following inflected word, causing over-redaction. |
| Kurmanji | Experimental transfer only. Detected Roj but missed surname Azad; hybrid covered email. Do not claim reliable Kurmanji support. |

Locations in the demos are public city names in invented sentences, not anyone's disclosed residence. Names are fictional characters, not collected contacts. Street-address parsing, full PII coverage, unseen languages and reliable de-identification are unsupported.
