from __future__ import annotations

import argparse
from importlib import import_module
import json
from pathlib import Path
import socket
import sys
from typing import Any, Callable

from src.doctor.batch import BatchPriorityCalculator, BatchRequest
from src.doctor.batch.queue import BatchQueueService, NightlyBatchWorker
from src.doctor.batch.queue.operations_log import JsonlOperationsLog
from src.doctor.batch.queue.sqlite_repository import SQLiteBatchQueueRepository


def load_executor(spec: str) -> Callable[[dict[str, Any], str, str], dict[str, Any]]:
    if ":" not in spec:
        raise ValueError("Executor must use module:function notation")
    module_name, function_name = spec.split(":", 1)
    function = getattr(import_module(module_name), function_name)
    if not callable(function):
        raise TypeError(f"Executor is not callable: {spec}")
    return function


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_service(database: Path, repository_root: Path) -> tuple[BatchQueueService, dict[str, Any]]:
    batch_policy = load_json(repository_root / "knowledge/batch/batch_policy_v1.json")
    queue_policy = load_json(repository_root / "knowledge/batch/batch_queue_policy_v1.json")
    service = BatchQueueService(
        repository=SQLiteBatchQueueRepository(database),
        policy=queue_policy,
        priority_calculator=BatchPriorityCalculator(batch_policy),
    )
    return service, queue_policy


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="sims-doctor-batch")
    result.add_argument("--database", required=True, type=Path)
    result.add_argument("--repository-root", type=Path, default=Path.cwd())
    result.add_argument("--log", type=Path)
    sub = result.add_subparsers(dest="command", required=True)

    enqueue = sub.add_parser("enqueue")
    enqueue.add_argument("--request", required=True, type=Path)

    run = sub.add_parser("run")
    run.add_argument("--queue-id")
    run.add_argument("--executor", required=True)
    run.add_argument("--owner", default=f"{socket.gethostname()}-scheduler")

    sub.add_parser("status").add_argument("--queue-id", required=True)
    sub.add_parser("list-incomplete")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    service, queue_policy = build_service(args.database, args.repository_root)
    operations = JsonlOperationsLog(args.log) if args.log else None

    try:
        if args.command == "enqueue":
            request = BatchRequest.from_dict(load_json(args.request))
            record = service.enqueue(request)
            if operations:
                operations.write("CLI_BATCH_ENQUEUED", {
                    "queue_record_id": record["queue_record_id"]
                })
            print(json.dumps(record, ensure_ascii=False))
            return 0

        if args.command == "status":
            record = service.repository.get(args.queue_id)
            if record is None:
                print(f"Queue record not found: {args.queue_id}", file=sys.stderr)
                return 4
            print(json.dumps(record, ensure_ascii=False))
            return 0

        if args.command == "list-incomplete":
            print(json.dumps(service.list_incomplete(), ensure_ascii=False))
            return 0

        executor = load_executor(args.executor)
        worker = NightlyBatchWorker(
            queue_service=service,
            item_executor=executor,
            policy=queue_policy,
        )
        if args.queue_id:
            results = [worker.run_once(args.queue_id, owner=args.owner)]
        else:
            results = worker.run_incomplete(owner_prefix=args.owner)
        if operations:
            for record in results:
                operations.write("CLI_BATCH_CYCLE_FINISHED", {
                    "queue_record_id": record["queue_record_id"],
                    "status": record["status"],
                    "progress": record["progress"],
                })
        print(json.dumps(results, ensure_ascii=False))
        if any(record["status"] == "FAILED" for record in results):
            return 3
        if any(record["status"] in {"PAUSED", "COMPLETED_WITH_ERRORS"} for record in results):
            return 2
        return 0
    except Exception as exc:
        if operations:
            operations.write("CLI_BATCH_ERROR", {
                "code": exc.__class__.__name__, "message": str(exc)
            })
        print(f"{exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
