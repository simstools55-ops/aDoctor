# SIMS Blog Manager ↔ SIMS Article Doctor Batch Integration

SBM responsibilities:

- create the batch request
- retain `batch_request_id` and `queue_record_id`
- poll status
- import a terminal result package
- store the result fingerprint
- return an import acknowledgement

Doctor responsibilities:

- validate the request
- enqueue isolated article cases
- expose safe progress
- export terminal results
- never expose the Medical Record
