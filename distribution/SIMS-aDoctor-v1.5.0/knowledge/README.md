# SIMS Article Doctor Clinical Knowledge Base v1.0

`knowledge/` is the declarative source of truth for Doctor's clinical workflow.

## Layer rule

1. Observation records facts and does not evaluate them.
2. Evidence extracts diagnostically meaningful facts.
3. Vital Signs express health on a 0–100 scale.
4. Findings describe phenomena and carry severity.
5. Differential Diagnosis lists competing hypotheses.
6. Final Diagnosis selects the supported diagnosis.
7. Treatment Recommendation selects a treatment direction.
8. Referral creates a product-specific referral request.

## Runtime rule

Thresholds, code registries, classifications, and allowed transitions belong here.
Runtime code must load and validate this knowledge instead of duplicating it.

## Sprint3.1 boundary

This release implements registries and the loading/validation foundation.
It does not calculate SEO scores, create findings, or produce diagnoses yet.
