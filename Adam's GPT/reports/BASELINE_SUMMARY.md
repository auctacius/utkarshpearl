# Actual development fixture results
48 fictional development records; eight per language, seven gold entities per language. Each language: TP=3, FP=0, FN=4, exact precision 1.0, recall 0.428571, F1 0.600000. Languages: en, ku, hi, zh, es, tr. Overall: TP=18, FP=0, FN=24. Macro-language F1=0.6; max-minus-min gap=0.0. Character redaction recall=0.493827.

This is a deliberately small software smoke set, used during development. Repeated shared email/phone payloads make identical language scores unsurprising. These scores cannot establish fairness, safety or real-world performance. PERSON/LOCATION recall is zero. Full predictions and gold outputs are in baseline_results.json; its dataset_sha256 identifies the exact fixture file. No held-out or learned-model results exist yet.

Executed example: `Email student@example.com; phone +1-202-555-0100.` -> `Email [EMAIL]; phone [PHONE].`
