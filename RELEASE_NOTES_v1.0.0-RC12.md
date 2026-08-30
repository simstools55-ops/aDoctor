# SIMS Doctor v1.0.0 RC12

## SBM Orchestration and Treatment Referral

RC12 aligns Doctor with SIMS Shared Editorial Knowledge v3.2.0.

### Added

- Accept `SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2` through a compatibility adapter.
- Preserve a CaseID issued by SIMS-Blog-Manager.
- Add `SIMS_DOCTOR_CASE_RESULT_V2`.
- Return structured Diagnosis, Treatment Plan, Referral, Workflow, and Reexamination data to SBM.
- Add `allowed_scope` and `blocked_scope` to the referral result.
- Mark direct Doctor-to-specialist invocation as deprecated.
- Add the V2 JSON Schema and RC12 regression tests.

### Compatibility

- Existing V1 request and result fields remain available.
- Legacy Writer request generation remains in the repository for compatibility but is not the standard orchestration path.
- Diagnosis engines and clinical rules are unchanged from RC4.
