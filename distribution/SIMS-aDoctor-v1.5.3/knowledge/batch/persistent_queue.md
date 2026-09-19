# Persistent Batch Queue

The persistent queue stores batch and item state outside a single process.

It provides:

- enqueue
- lease-based locking
- checkpoint persistence
- pause and resume
- retry scheduling
- expired-lock recovery
- progress and completion events

The queue abstraction is storage-neutral. A deployment adapter may use a database,
object store, spreadsheet, or another durable backend.
