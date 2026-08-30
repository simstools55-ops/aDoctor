# Differential Diagnosis Rules v1

Differential Diagnosis creates ranked hypotheses. It does not confirm a final diagnosis.

Each candidate contains:

- diagnosis code
- supporting Findings
- contradicting Findings
- confidence
- evidence trace
- rank
- rule version

`INSUFFICIENT_DATA` may outrank other hypotheses when all available support is low-sample.
