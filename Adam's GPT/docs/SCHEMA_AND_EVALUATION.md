# Schema and evaluation contract
Version 0.1. Each JSONL record has id, language, script, text, entities, split, source and parallel_group. Language codes: en, ku (Kurmanji in this project, Latin script), hi, zh (Simplified Chinese), es, tr. No Arabic dataset is included. More languages require explicit data and reviewer support.

Entities are nonoverlapping {start,end,label} objects, using zero-based half-open Unicode code-point offsets into the ORIGINAL text. Do not normalize before scoring. Python string offsets are not UTF-8 bytes or JavaScript UTF-16 offsets. Reject invalid bounds, duplicate document IDs and duplicate texts. Nonoverlapping gold spans are required in v0.1.

Labels: PERSON = explicit full or partial personal name, excluding titles; EMAIL = entire email or explicitly labeled obfuscated email; PHONE = entire telephone string including country prefix and internal separators, excluding surrounding punctuation; LOCATION = explicitly mentioned city/locality. Street addresses are deferred: do not map partial address components to LOCATION silently. No legal definition of all PII is claimed.

Regex currently predicts EMAIL and international-format PHONE only. PERSON and LOCATION remain in the gold data and full-schema recall denominator. Report both full-schema and per-label scores; never hide unsupported classes.

Primary metric: exact (start,end,label) entity precision/recall/F1, one-to-one via unique span sets. Boundary or label errors count as both FP and FN. Report TP/FP/FN and document support per language and label; pooled micro and unweighted macro language F1. Undefined denominators are null, not a fabricated perfect score. Secondary: label-agnostic union-of-character precision/recall, measuring redaction coverage and over-redaction. Gap = maximum minus minimum language F1, descriptive only.

The 48 committed samples are DEVELOPMENT smoke fixtures used in implementation, not an independent test or training dataset. Equal scores cannot demonstrate parity: phone/email payloads are mostly identical across translations. There is no model training or held-out result in phase 1.

For phase 3: select licensed independent data, freeze SHA256 manifest and train/dev/test membership before tuning; group translated records, source-document families and near duplicates into the same split. Use train for fitting, dev for all thresholds and choices, test only for final comparisons. Preserve REDACT's locked split if adopted; exclude every locked ID from fitting/tuning. Balance language/type slices where feasible and report support, native-script digits, code switching and obfuscation separately. Add paired bootstrap confidence intervals grouped by source/translation family once samples support them. Require fluent-speaker checks and annotation audits; do not infer causality or population fairness from this fixture set.

Phase 2: AI and hybrid use the same labels/offsets and metric formulas. Model-selected LOCATION can overreach our locality-only gold policy; count mismatches honestly. No new held-out dataset or benchmark results were introduced. See MODEL.md for raw scores, tokenization and overlap policies.
