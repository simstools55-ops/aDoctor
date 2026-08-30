import json
from pathlib import Path

from src.doctor.batch import BatchPriorityCalculator, BatchRequest
from src.doctor.batch.queue import (
    BatchQueueService, NightlyBatchWorker, SQLiteBatchQueueRepository
)

ROOT = Path(__file__).resolve().parents[2]


def policies():
    batch = json.loads((ROOT / "knowledge/batch/batch_policy_v1.json").read_text(encoding="utf-8"))
    queue = json.loads((ROOT / "knowledge/batch/batch_queue_policy_v1.json").read_text(encoding="utf-8"))
    return batch, queue


def service(path):
    batch, queue = policies()
    return BatchQueueService(
        repository=SQLiteBatchQueueRepository(path),
        policy=queue,
        priority_calculator=BatchPriorityCalculator(batch),
    ), queue


def test_paused_batch_resumes_after_process_restart(tmp_path):
    request = BatchRequest.from_dict(json.loads(
        (ROOT / "tests/fixtures/batch/batch_request.json").read_text(encoding="utf-8")
    ))
    database = tmp_path / "queue.db"
    first_service, queue_policy = service(database)
    record = first_service.enqueue(request)
    queue_policy["execution"]["maximum_items_per_cycle"] = 1
    worker = NightlyBatchWorker(
        queue_service=first_service,
        item_executor=lambda item, case_id, key: {"result_status": "DIAGNOSED"},
        policy=queue_policy,
    )
    paused = worker.run_once(record["queue_record_id"], owner="worker-1")
    assert paused["status"] == "PAUSED"
    assert paused["progress"]["completed"] == 1

    second_service, second_policy = service(database)
    second_worker = NightlyBatchWorker(
        queue_service=second_service,
        item_executor=lambda item, case_id, key: {"result_status": "DIAGNOSED"},
        policy=second_policy,
    )
    completed = second_worker.run_once(record["queue_record_id"], owner="worker-2")
    assert completed["status"] == "COMPLETED"
    assert completed["progress"]["completed"] == 2
