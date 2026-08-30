# Clinical Pipeline v1

The pipeline coordinates existing Doctor components without merging their responsibilities.

```text
Request Reception
→ Search Console Observation
→ SERP Observation
→ Article Snapshot Observation
→ Evidence
→ Vital Signs
→ Findings
→ Differential Diagnosis
→ Final Diagnosis
→ Treatment Recommendation
→ Referral
```

Every step remains independently testable and idempotent.
The pipeline only coordinates order, failure handling, resume, and final result generation.
