# SIMS Doctor v1.2.0-RC1

## Purpose
Introduce Algorithm Impact Analysis as an external-evidence layer while preserving the established SBM → Doctor → SBM → specialist workflow.

## Added
- `SIMS_DOCTOR_ALGORITHM_IMPACT_ASSESSMENT_V1` contract.
- Algorithm Impact Analyzer and idempotent assessment service.
- Evidence-confidence metadata for algorithm evidence.
- Treatment Strategy: `WAIT`, `LIGHT_FIX`, `NORMAL_REWRITE`, `FULL_REWRITE`.
- WAIT plan, user ToDo, and evidence-based reassurance guidance.
- Case Result V2 optional algorithm/treatment-strategy fields.

## Safety rules
- Google update overlap alone never establishes causation.
- Algorithm evidence does not replace Search Console, SERP, article, site, or treatment-history evidence.
- Severe content-integrity issues can block algorithm-driven waiting.
- Doctor still returns to SBM; direct specialist invocation remains disabled.

## Compatibility cleanup
- Updated stale tests that still expected the pre-platform direct-specialist handoff.
- Historical release event manifests remain immutable and are validated as subsets of the current registry.
