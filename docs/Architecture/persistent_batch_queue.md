# Persistent Batch Queue and Nightly Worker

## Queue

The queue record stores item state, attempts, retry timing, progress, lock ownership,
and lifecycle events.

## Locking

A worker acquires a lease. An active lease blocks other workers. Expired leases may be reclaimed.

## Checkpoints

Every completed or failed item updates the durable queue record.

## Nightly execution

The worker processes items until either:

- no eligible item remains
- the maximum items per cycle is reached
- the runtime budget is reached

An incomplete batch is paused and can be resumed during the next cycle.
