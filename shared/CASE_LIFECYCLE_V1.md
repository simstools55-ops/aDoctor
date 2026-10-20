# SIMS Editorial Platform Case Lifecycle v1.0

## Principle

A Case represents one diagnosis-treatment-measurement-re-examination cycle. An article may have multiple Cases over time.

## Identifier format

```text
CASE-YYYYMMDD-ARTICLEID-NNN
```

Example:

```text
CASE-20260805-A999999-001
```

SBM issues the CaseID before sending a Doctor request.

## Records linked to a Case

- SiteID and ArticleID
- Doctor diagnosis request
- Doctor diagnosis result
- Treatment Plan and Referral
- Writer treatment request
- Writer treatment result
- User publication decision
- Publication confirmation
- Improvement History ID
- 7/14/21/28-day measurements
- Doctor re-examination result
- Completion or cancellation reason

## Standard transitions

### Monitor only

```text
DOCTOR_DIAGNOSIS_PENDING
-> DOCTOR_DIAGNOSED
-> MONITORING
-> REEXAMINATION_PENDING
-> COMPLETED
```

### Writer treatment

```text
DOCTOR_DIAGNOSIS_PENDING
-> DOCTOR_DIAGNOSED
-> TREATMENT_REVIEW_PENDING
-> WRITER_REQUEST_READY
-> WRITER_IN_PROGRESS
-> TREATMENT_RESULT_RECEIVED
-> PUBLICATION_PENDING
-> MONITORING
-> REEXAMINATION_PENDING
-> COMPLETED
```

### Existing SBM monitoring lock

```text
DOCTOR_DIAGNOSIS_PENDING
-> DOCTOR_DIAGNOSED
-> WORKFLOW_LOCKED
-> TREATMENT_REVIEW_PENDING
```

The transition out of `WORKFLOW_LOCKED` is performed by SBM after the active monitoring condition ends or the user explicitly resolves it.

## State ownership

- SBM stores and changes authoritative Case state.
- Doctor recommends actions and re-examination conditions.
- Writer reports treatment progress and result status.
- User approval and publication events are recorded by SBM.

## Idempotency

A repeated message with the same `message_id`, `diagnosis_id`, or `treatment_result_id` must not create a duplicate Case event.
