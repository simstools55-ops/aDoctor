# Evidence Engine

Evidence converts immutable Observation facts into traceable diagnostic facts.

## Guarantees

- every Evidence references one or more Observation IDs
- thresholds are loaded from CKB
- every Evidence stores measured values and comparison basis
- LOW_SAMPLE is retained as a flag rather than discarded
- a deterministic fingerprint prevents duplicate generation
- every saved Evidence creates an `EVIDENCE_RECORDED` event

Evidence does not create Vital Signs, Findings, or Diagnoses.
