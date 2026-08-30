# SIMS Editorial Platform Interface Contract Registry v2.0.0

## 1. Purpose

This registry defines the canonical minimum workflow connecting SIMS-Blog-Manager, SIMS Article Doctor, and SIMS Writer.

The platform orchestration rule is:

```text
SBM -> Doctor -> SBM -> Writer -> SBM -> measurement -> Doctor re-examination
```

SIMS-Blog-Manager is the system of record for Case state, workflow history, requests, results, publication status, and performance measurement.

## 2. Canonical contracts

| Contract | Source | Target | Responsibility |
|---|---|---|---|
| `SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2` | SBM | Doctor | Individual diagnosis request and Evidence Package |
| `SIMS_DOCTOR_CASE_RESULT_V2` | Doctor | SBM | Diagnosis, Treatment Plan, Referral, and re-examination conditions |
| `SIMS_WRITER_TREATMENT_REQUEST_V1` | SBM | Writer | Doctor-referred treatment request with allowed and blocked scope |
| `SIMS_WRITER_TREATMENT_RESULT_V1` | Writer | SBM | Treatment result, referral compliance, and publication readiness |
| `SIMS_DOCTOR_REEXAMINATION_REQUEST_V1` | SBM | Doctor | Post-treatment re-examination evidence |

## 3. Ownership rules

- `site_id` and `article_id` are issued and owned by SBM.
- `case_id` is issued and owned by SBM.
- `diagnosis_id` is issued by Doctor and stored by SBM.
- `treatment_request_id` is issued by SBM.
- `treatment_result_id` is issued by the treatment product and stored by SBM.
- `improvement_history_id` remains owned by SBM.
- Every sender issues a unique `message_id`; duplicate messages are handled idempotently.

## 4. Routing rules

- Doctor never directly invokes Writer, Creator, or Merge.
- Doctor returns a diagnosis, Treatment Plan, and Referral to SBM.
- SBM validates the Referral, checks Workflow Lock, and creates the treatment request.
- Writer returns the treatment result to SBM, not to Doctor.
- Doctor receives a new request only when SBM requests diagnosis or re-examination.
- Creator and Merge will use the same SBM-mediated routing model when connected.

## 5. Case lifecycle source of truth

SBM is the only source of truth for Case lifecycle state.

Canonical minimum states:

```text
DOCTOR_DIAGNOSIS_PENDING
DOCTOR_DIAGNOSED
TREATMENT_REVIEW_PENDING
WRITER_REQUEST_READY
WRITER_IN_PROGRESS
TREATMENT_RESULT_RECEIVED
PUBLICATION_PENDING
MONITORING
REEXAMINATION_PENDING
COMPLETED
```

Exception states:

```text
WORKFLOW_LOCKED
USER_DECISION_REQUIRED
EVIDENCE_INSUFFICIENT
TREATMENT_FAILED
PUBLICATION_VERIFICATION_REQUIRED
CANCELLED
```

Doctor and Writer may report facts relevant to state transitions, but they do not authoritatively change the Case state.

## 6. Treatment scope rules

A Doctor Referral may define:

- `allowed_scope`
- `blocked_scope`
- `treatment_level`
- `objective`
- `reason_codes`
- `priority`
- `review_after_days`

Writer must not modify a blocked scope. A scope conflict or violation is returned to SBM as `USER_DECISION_REQUIRED` or `BLOCKED` and must not be silently normalized.


## 6A. Algorithm and Treatment Strategy extensions

Doctor case results may include additive, backward-compatible fields for:

- Algorithm Impact Assessment
- Evidence Confidence metadata
- Treatment Strategy: `WAIT`, `LIGHT_FIX`, `NORMAL_REWRITE`, `FULL_REWRITE`
- WAIT observation/re-examination plan
- User-facing ToDo
- Evidence-based guidance / reassurance

Algorithm information is Evidence, not a standalone diagnosis. Doctor must not route treatment directly from an update-date match. Site-wide impact evidence may be supplied by SBM as an aggregated Evidence Package component.

These extensions do not change the canonical routing path: `Doctor -> SBM -> specialist`.

## 7. Workflow Lock

- Doctor may diagnose while an SBM monitoring lock exists.
- Doctor cannot release, replace, or bypass an SBM lock.
- SBM decides whether a treatment request may be generated.
- A Referral received during a lock is stored and held until SBM permits the next transition.

## 8. Compatibility

`doctor/INTERFACE_CONTRACTS_V1.md` is retained only for historical compatibility.

The following V1 routing is deprecated:

```text
Doctor -> Writer
Writer -> Doctor
Doctor-owned case_id
```

New implementations must use this V2 registry. Existing V1 messages may be read by adapters, but must not be emitted as the preferred platform path.
