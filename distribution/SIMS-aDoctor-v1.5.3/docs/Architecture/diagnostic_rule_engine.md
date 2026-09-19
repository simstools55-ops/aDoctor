# Diagnostic Rule Engine

The Diagnostic Rule Engine evaluates declarative rules against the Medical Record.

## Input sources

- Evidence
- Findings
- Vital Signs
- Observations
- Longitudinal Profile
- Treatment History
- Case Context

## Output

The engine produces diagnosis candidates with:

- confidence
- severity
- priority
- matched rule
- explanation
- supporting Evidence and Findings

## Separation of responsibility

The engine does not create a Final Diagnosis or Referral.
It only produces explainable candidates for the existing Differential and Final Diagnosis layers.
