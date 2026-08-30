# Batch Doctor Foundation

Batch Doctor executes the existing single-case workflow for many articles.

## Guarantees

- every article has an independent Case
- one failed item does not stop the batch
- priority is calculated before execution
- completed items can be skipped during resume
- failed items can be retried up to the policy limit
- output remains compatible with the single-case result contract

## Not included

This foundation does not include a persistent worker, scheduler, or night-time execution service.
