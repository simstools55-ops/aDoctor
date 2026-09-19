# Medical Record Event Log

## Purpose

The event log records append-only clinical history while the medical record retains
readable projections such as `observations`.

## Guarantees

- contiguous sequence numbers
- unique event IDs
- optional idempotency key
- identical replay returns the original event
- conflicting replay is rejected
- SHA-256 payload hash detects accidental or unauthorized mutation

The payload hash is an integrity check, not a digital signature.
Persistent storage transactions are implemented by the repository adapter in a later sprint.
