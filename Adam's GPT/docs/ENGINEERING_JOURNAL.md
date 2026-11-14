# PIIParity Engineering Journal
Complete phase-1 engineering record. Times are UTC unless stated. This records actions and evidence, not hidden reasoning. Exported in full by experiments/export_journal.py.

## Scope and ownership
Project: PIIParity, AI + Languages, Veritas AI International High School Hackathon 2026. User requested direct execution and all artifacts under Adam's GPT/. Current client date November 14, 2026; confirmed clock reading during setup: 2026-11-14 19:18:58 UTC (14:18:58 ET). Development in this session is within the official window. Deadline: November 15 23:59 ET / November 16 04:59 UTC / November 15 22:59 Chicago.
Human contribution evidenced: user supplied project concept, rules, research constraints and repository target. User then confirmed Hindi, replaced Arabic with Kurmanji and requested language variety. Assistant added Spanish and Turkish to English, Kurmanji, Hindi and Simplified Chinese. No human linguistic validation or student implementation is claimed. Fluent-speaker review and student understanding remain required.

## Source and compliance audit - before 19:18:58 UTC
Actions: connected GitHub search_installed_repositories_v2(query=utkarshpearl); search_branches(owner=auctacius, repo_name=utkarshpearl). Results: exact repository auctacius/utkarshpearl, ID 1457400547, private, main default, write permission; no branches returned. No unrelated files changed.
Commands attempted: gh auth status (failed: gh not installed); git ls-remote https://github.com/auctacius/utkarshpearl.git (failed: host resolution in local environment). Switched to authenticated connected GitHub write tools; did not expose tokens, install another connection or force-push.
Actions: read full text of both official PDFs through google_drive_fetch. Hacker Guide sections 8-10 and Project Brief pages 1-4, 15-22 were examined for requirements. Brief fixes exact window and says AI must perform the main job. Regex is only a comparator. Documentation: docs/COMPLIANCE.md contains completed and pending items and source conflicts.
Hacker Guide: https://drive.google.com/file/d/1_XIisoApHfiuIzkPev6hKJ4SlViGH4pm/view
Project Brief: https://drive.google.com/file/d/15tYD48XRmCgWbk1_lLDtc8lebi6qm-4-/view
Conflict: Guide describes required video, kickoff and a placeholder time. Specific Brief states optional video, no kickoff and exact deadline. Plan a video anyway; use Brief for times. No organizer approval or contact is claimed.

## Dataset decision - 19:18 to 19:21 UTC
Actions: web search for REDACT multilingual PII; opened REDACT card, LICENSE and ai4privacy pii-masking-300k card. REDACT has relevant span annotations but gated access and custom terms, not an unrestricted MIT data license. Kurmanji is absent from the card's language list. Did not accept gated terms or download corpus. ai4privacy preview was readable, but full license/target-language review was incomplete; did not ingest it. See data/README.md for source links, provenance and selection rationale.
Selected phase-1 executable data: 48 original AI-authored fictional development records, 8 per language. No private texts collected; example domains and fictional phone range used. A public benchmark was not acquired; independent evaluation remains pending. Ground truth is construction-defined and not fluent-speaker-validated. Never report this as held-out data.
Schema decision: four labels PERSON, EMAIL, PHONE, LOCATION; half-open Unicode code-point spans in unchanged text. Addresses deferred. Negative controls and obfuscated/local-format cases retained. Shared translation-family identifiers reserved for future group-safe splitting.

## Implementation and actual checks - 19:18 to 19:22 UTC
Action: created src/, data/, experiments/, tests/, docs/, reports/, submission/, pyproject.toml and scoped .gitignore. Python standard-library pipeline supports local stdin inference and JSONL evaluation. Regex handles ASCII emails and plus-prefixed international phones; names and locations unsupported. Deterministic overlap resolution and reverse-order replacement preserve offsets.
Command: PYTHONPATH=src python3 -m unittest discover -s tests -v.
Initial outcome: 15 tests passed, 1 failed because Kurmanji and Turkish used identical phone-context text, triggering duplicate-text validation. Evaluation also failed on the same duplicate check. Correction: changed Kurmanji context to distinct wording and shifted its gold offsets by 9 code points. No weakening of duplicate validation.
Repeated test command: all 16 tests passed. Tests cover emoji/Chinese offsets, Devanagari digits, invalid/overlapping spans, repeated entities, punctuation, negatives, empty inputs, known unsupported cases, wrong labels/boundaries and undefined metrics. Output saved in reports/test_results.txt.
Command: PYTHONPATH=src python3 -m piiparity evaluate data/smoke.jsonl > reports/baseline_results.json. Outcome: exit 0, 48 records. Full per-language/per-label counts and side-by-side gold/predicted spans and redactions persisted.
Command: printf 'Email student@example.com; phone +1-202-555-0100.' | PYTHONPATH=src python3 -m piiparity redact. Outcome: Email [EMAIL]; phone [PHONE]. JSON spans [6,25) EMAIL and [33,48) PHONE. Exit 0.
Observed results: TP=18, FP=0, FN=24; full-schema precision=1.0, recall=0.428571, F1=0.6. Each language has TP=3, FP=0, FN=4, F1=0.6. Macro language F1=0.6 and gap=0.0. PERSON/LOCATION recall=0. Character coverage recall=0.493827. Identical fixture scores are NOT evidence of parity. No learned model, model weights, training or independent test was run.
Dataset SHA256: 335388a257d7e1a87f22e7d7ed5a71b11ce856391a3839c36043c7800dbd6de9.
Environment: Python 3.12.14; core has no third-party dependencies. ReportLab 4.4.9. Attempted PyMuPDF import failed (not installed); chose available pypdfium2 for rendering and pypdf for extraction. PDF creation is ancillary and separate from core inference.

## Publication and documentation
2026-11-14 19:21:42 UTC: GitHub create_file initialized Adam's GPT/README.md. Returned commit d9fa9e381d3e570414eadf08bf544bdcd89ba61c. Independently fetched that commit and verified its path/content. This bootstrap commit was necessary because the repository had no branch; remaining artifacts are prepared for the phase commit.
Documentation created: architecture, compliance checklist, schema/evaluation, data provenance/selection, credits and actual human contribution ledger, setup README, baseline summary, submission staging and this editable journal. PDF exporter includes every nonblank journal line in order, with pagination, without summarization.
Record prepared at 2026-11-14T19:22:51.273266+00:00. Phase files will be published through Git blob/tree/commit APIs using the current branch as parent and a non-forced guarded reference update. Remote publication is not claimed here before it happens. Final commit SHA is reported separately after readback because a commit cannot embed its own SHA. No unrelated paths or visibility changes are authorized by this phase.

PDF QA: rendered the initial three-page PDF and inspected all pages; detected a paragraph split onto a sparse last page, adjusted line spacing and margins for a more compact export. Text extraction check accounts for pagination footers.

## Remaining requirements and next phase
Implement and actually run a learned multilingual detector; verify and pin its license/revision/dependencies. Acquire an independent licensed benchmark with useful Kurmanji coverage, validate offset/label mapping, and freeze grouped splits before tuning. Get students to review code, contribute documented changes, check language examples and explain all components. Confirm fluent-language reviewers. Prepare accessible submission code/write-up and a short demo before deadline. Current private repository is not anonymously accessible. No submission, public sharing or success/ranking claim has been made.
