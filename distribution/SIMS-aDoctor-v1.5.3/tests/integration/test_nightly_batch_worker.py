from pathlib import Path
import json

from src.doctor.batch import BatchPriorityCalculator, BatchRequest
from src.doctor.batch.queue import (
    BatchQueueService, InMemoryBatchQueueRepository, NightlyBatchWorker
)


ROOT = Path(__file__).resolve().parents[2]


def setup(executor):
    request = BatchRequest.from_dict(json.loads(
        (ROOT / "tests/fixtures/batch_queue/batch_request.json")
        .read_text(encoding="utf-8")
    ))
    queue_policy = json.loads(
        (ROOT / "knowledge/batch/batch_queue_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    batch_policy = json.loads(
        (ROOT / "knowledge/batch/batch_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = BatchQueueService(
        repository=InMemoryBatchQueueRepository(),
        policy=queue_policy,
        priority_calculator=BatchPriorityCalculator(batch_policy),
    )
    record = service.enqueue(request)
    worker = NightlyBatchWorker(
        queue_service=service,
        item_executor=executor,
        policy=queue_policy,
    )
    return record, service, worker


def test_worker_completes_batch():
    def executor(item, case_id, run_key):
        return {
            "result_status": "DIAGNOSED",
            "referral": {"target": "WRITER"},
        }

    record, _, worker = setup(executor)
    result = worker.run_once(record["queue_record_id"], owner="night-1")
    assert result["status"] == "COMPLETED"
    assert result["progress"]["completed"] == 2
    assert result["lock"] is None


def test_worker_continues_after_failure_and_schedules_retry():
    def executor(item, case_id, run_key):
        if item["article_id"] == "A2":
            raise RuntimeError("temporary failure")
        return {"result_status": "DIAGNOSED"}

    record, _, worker = setup(executor)
    result = worker.run_once(record["queue_record_id"], owner="night-2")
    assert result["status"] == "PAUSED"
    assert result["progress"]["completed"] == 1
    assert result["progress"]["failed"] == 1
    failed = [item for item in result["items"] if item["status"] == "FAILED"][0]
    assert failed["next_attempt_at"] is not None


def test_execution_budget_pauses_and_resume_completes():
    calls = []

    def executor(item, case_id, run_key):
        calls.append(item["article_id"])
        return {"result_status": "DIAGNOSED"}

    record, service, worker = setup(executor)
    worker.policy["execution"]["maximum_items_per_cycle"] = 1
    first = worker.run_once(record["queue_record_id"], owner="night-3")
    assert first["status"] == "PAUSED"
    assert first["progress"]["completed"] == 1

    worker.policy["execution"]["maximum_items_per_cycle"] = 25
    second = worker.run_once(record["queue_record_id"], owner="night-4")
    assert second["status"] == "COMPLETED"
    assert second["progress"]["completed"] == 2
    assert len(calls) == 2
