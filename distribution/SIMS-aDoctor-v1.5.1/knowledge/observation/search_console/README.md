# Search Console Acquisition Policy

Doctor requests 365 days of Search Console data with a three-day data-lag buffer.

The acquisition layer:

- retrieves page-level aggregate metrics
- retrieves query-level rows with paging
- derives 28-day, 90-day, and 365-day periods
- reports COMPLETE, PARTIAL, FAILED, or NO_DATA
- converts the result into `SIMS_DOCTOR_SEARCH_CONSOLE_OBSERVATION_INPUT_V1`

OAuth credentials and Google client construction belong to deployment adapters, not Knowledge.
