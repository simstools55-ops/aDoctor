# SBM Batch Integration

This integration connects SIMS Blog Manager and SIMS Article Doctor only through JSON contracts.

Flow:

1. SBM submits a batch request.
2. Doctor validates and enqueues it.
3. SBM polls a status contract.
4. Doctor exports a terminal result package.
5. SBM imports the package and returns an idempotent acknowledgement.

Doctor does not expose Medical Records to SBM.
