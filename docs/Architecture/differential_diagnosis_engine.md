# Differential Diagnosis Engine

The engine ranks possible diagnoses from the current Findings.

## Output

- candidate diagnosis code
- rank
- confidence
- supporting Finding IDs
- contradicting Finding IDs
- Evidence IDs
- rationale
- rule version

## Safety boundary

Differential candidates are hypotheses only.
No candidate is a Final Diagnosis until the Final Diagnosis Engine applies confirmation,
minimum-confidence, contradiction, and data-quality rules.
