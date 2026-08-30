# Findings Engine

The Findings Engine converts Evidence and the latest Vital Profile into explainable
clinical findings.

## Guarantees

- every finding references Evidence IDs
- every finding references the Vital Profile used
- severity is derived from Knowledge rules
- LOW_SAMPLE reduces confidence
- identical fingerprints are not stored twice
- every saved finding emits `FINDING_RECORDED`

A Finding is not a Final Diagnosis.
