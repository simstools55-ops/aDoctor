# SBM Batch Integration

## Contracts

- `SIMS_SBM_DOCTOR_BATCH_REQUEST_V1`
- `SIMS_SBM_DOCTOR_BATCH_ACCEPTED_V1`
- `SIMS_SBM_DOCTOR_BATCH_STATUS_V1`
- `SIMS_SBM_DOCTOR_BATCH_RESULT_PACKAGE_V1`
- `SIMS_SBM_DOCTOR_BATCH_IMPORT_ACK_V1`

## Boundary

SBM sends article identity, single-case requests, optional current metrics, and optional
longitudinal priority data. Doctor returns progress and final result packages.

Medical Records, raw Evidence, internal Findings, and diagnostic rule internals are not
exported to SBM.

## Idempotency

Repeated submission of the same batch request returns the existing queue.
Repeated import of the same result fingerprint returns `ALREADY_IMPORTED`.
