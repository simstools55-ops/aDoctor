# Clinical Workflow v1.0

```text
Request
  → Medical Record
  → Observation
  → Evidence
  → Vital Signs
  → Findings
  → Differential Diagnosis
  → Final Diagnosis
  → Treatment Recommendation
  → Referral
  → Follow-up
```

## Separation of duties

- SBM requests diagnosis and manages operations.
- Doctor owns observation, evidence, findings, diagnosis, the medical record, and referrals.
- Writer performs rewrite treatment.
- Creator creates a new article when referred.
- Merge performs article integration in the future.
