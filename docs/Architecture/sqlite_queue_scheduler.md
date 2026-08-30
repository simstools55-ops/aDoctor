# SQLite Queue Adapter and Scheduler CLI

`SQLiteBatchQueueRepository` is the first production-capable durable adapter. It uses
SQLite WAL mode, full synchronous writes, a busy timeout, and atomic transactions.

The scheduler CLI supports:

- enqueue a batch request
- run one queue or every incomplete queue
- inspect queue status
- list incomplete queues
- emit JSON Lines operations logs

The treatment executor is loaded as `module:function`, keeping deployment-specific
credentials and orchestration outside the queue package.
