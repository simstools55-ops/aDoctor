# SIMS Article Doctor v1.3.1

## Personal Knowledge Separation

This MINOR release makes the standard Article Doctor distribution tenant-neutral.

- Replaced real blog/site fixtures with `example.invalid`, `sample-site`, and synthetic site names.
- Replaced the retained real operational Article/Case example with synthetic `A999999`.
- Preserved `SIMS_DOCTOR_*`, request/response schemas, Case/Batch contracts, diagnosis logic, and Shared v3.5.0 compatibility baseline.
- No Claude API integration is introduced.

No destructive migration of existing operational data is required.
