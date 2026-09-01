# Diagnostic Rule Engine

Rules are declarative and do not contain article-editing logic.

A rule defines:

- target diagnosis
- required conditions
- confidence baseline
- severity
- priority
- explanation
- mutual exclusion group

The engine evaluates rules against the Medical Record and produces diagnosis candidates.
Final Diagnosis and Treatment remain separate layers.
