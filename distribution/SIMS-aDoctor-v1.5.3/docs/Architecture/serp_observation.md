# SERP Observation

## Boundary

A provider adapter retrieves raw SERP data. `SerpAcquisitionService` normalizes it into
`SIMS_DOCTOR_SERP_OBSERVATION_INPUT_V1`. `SerpObservationService` records it in the
Medical Record.

## Recorded facts

- top result titles, URLs, domains, snippets, and positions
- primary intent and confidence
- SERP features
- normalized competition metrics
- differences from the previous snapshot

## Vital Sign integration

SERP Observation enables `COMPETITION_RESILIENCE`.
`CONTENT_INTEGRITY` remains unavailable until Article Snapshot Observation is implemented.
