from pathlib import Path
import json
import pytest

from src.doctor.batch import BatchPriorityCalculator, BatchRequest
from src.doctor.batch.queue import (
    BatchQueueService, BatchLockError, InMemoryBatchQueueRepository
)


ROOT = Path(__file__).resolve().parents[2]


def build():
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
    return request, service


def test_enqueue_is_idempotent():
    request, service = build()
    first = service.enqueue(request)
    second = service.enqueue(request)
    assert first["queue_record_id"] == second["queue_record_id"]
    assert first["progress"]["total"] == 2


def test_lock_blocks_other_worker():
    request, service = build()
    record = service.enqueue(request)
    service.acquire(record["queue_record_id"], "worker-1")
    with pytest.raises(BatchLockError):
        service.acquire(record["queue_record_id"], "worker-2")


def test_complete_item_updates_checkpoint():
    request, service = build()
    record = service.enqueue(request)
    queue_id = record["queue_record_id"]
    service.acquire(queue_id, "worker")
    item = service.next_item(queue_id, "worker")
    saved = service.complete_item(
        queue_id,
        "worker",
        item["item_id"],
        case_id="CASE-1",
        result={"result_status": "DIAGNOSED"},
    )
    assert saved["progress"]["completed"] == 1
    assert any(
        event["event_type"] == "BATCH_PROGRESS_UPDATED"
        for event in saved["events"]
    )
