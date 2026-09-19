# SIMS Article Doctor v1.0.0-RC1 Architecture Freeze

SIMS Article Doctor diagnoses existing articles and determines treatment policy.

Doctor may diagnose, maintain Medical Records, compare long-term performance and SERP
evidence, determine treatment policy, and create referrals.

Doctor may not edit, publish, delete, noindex, redirect, or merge articles.

```text
SIMS Blog Manager
        ↓ JSON
SIMS Article Doctor
        ↓ JSON referral
Writer / Creator / Merge
        ↓
User operation
```

`SIMS_DOCTOR_MEDICAL_RECORD_V1` is the diagnostic Single Source of Truth.
