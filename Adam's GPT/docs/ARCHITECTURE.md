# Architecture
UTF-8 stdin -> regex candidate detector -> deterministic overlap resolution -> validated original-text spans -> reverse-order replacement -> JSON stdout. No network, persistent input log, telemetry, model weights or secret is required. Maximum recommended interactive input is a short paragraph; regex is not a security guarantee.

Offline evaluation reads annotated JSONL -> validates spans and unique records -> exact entity and character-coverage scoring -> per-language/per-label results plus side-by-side examples. Stable dataset SHA256 ties results to input. Data and gold annotations are never provided to the detector.

Next phase: add a separate learned detector with the same Span interface; pin model identifier/revision, license, dependency versions and inference settings. Keep regex as an unchanged comparator. Evaluate model-only and hybrid variants independently. No AI inference is implemented yet.
