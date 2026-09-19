# Clinical Pipeline Orchestrator

The orchestrator coordinates Doctor's independent clinical components.

## Responsibilities

- step order
- observation failure tolerance
- clinical failure stop
- idempotent resume
- final pipeline result
- pipeline completion event

## Non-responsibilities

The orchestrator contains no SEO thresholds, diagnosis rules, formulas, or referral rules.
Those remain in CKB and the relevant domain engines.
