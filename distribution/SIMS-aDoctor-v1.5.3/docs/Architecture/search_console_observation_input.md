# Search Console Observation Input v1

Doctor accepts 28-day, 90-day, and 365-day aggregates plus query-level metrics.

Retrieval status:

- `COMPLETE`: requested coverage was obtained
- `PARTIAL`: some dates or rows are missing
- `FAILED`: retrieval failed and an error code is required
- `NO_DATA`: retrieval succeeded but Search Console returned no data

This model does not calculate Evidence, Vital Signs, Findings, or Diagnosis.
