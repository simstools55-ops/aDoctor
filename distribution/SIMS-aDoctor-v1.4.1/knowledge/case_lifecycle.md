# Case Lifecycle v1

## Sprint2-1 active states

| State | Meaning | Next state |
|---|---|---|
| OPEN | Case ID has been reserved | REQUEST_VALIDATED or ERROR |
| REQUEST_VALIDATED | External request passed validation | RECORD_CREATED or ERROR |
| RECORD_CREATED | Medical record was created | READY_FOR_OBSERVATION or ERROR |
| READY_FOR_OBSERVATION | Observation Engine may begin | OBSERVING |
| ERROR | Reception transaction failed | retry or manual review |

## Future states

`OBSERVING → DIAGNOSING → DIAGNOSED → REFERRED → UNDER_TREATMENT → FOLLOW_UP → CLOSED`

## Invariants

1. A case has exactly one medical record.
2. A medical record ID never changes.
3. An active case is identified primarily by `site_id + article_id`.
4. A second request for an active case is appended to the same medical record.
5. A closed case creates a new case in Doctor v1.0.
6. Registry commit and medical-record creation are one transaction.
7. Observation and diagnosis never read the raw SBM request directly.
