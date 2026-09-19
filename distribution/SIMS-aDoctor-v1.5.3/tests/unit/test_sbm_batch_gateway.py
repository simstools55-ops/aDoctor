from pathlib import Path
import json
import pytest

from src.doctor.batch import BatchPriorityCalculator
from src.doctor.batch.queue import BatchQueueService, InMemoryBatchQueueRepository
from src.doctor.integration.sbm import SbmBatchGateway, SbmIntegrationError


ROOT = Path(__file__).resolve().parents[2]


def build():
    queue_policy = json.loads(
        (ROOT / "knowledge/batch/batch_queue_policy_v1.json").read_text(encoding="utf-8")
    )
    batch_policy = json.loads(
        (ROOT / "knowledge/batch/batch_policy_v1.json").read_text(encoding="utf-8")
    )
    service = BatchQueueService(
        repository=InMemoryBatchQueueRepository(),
        policy=queue_policy,
        priority_calculator=BatchPriorityCalculator(batch_policy),
    )
    return service, SbmBatchGateway(service)


def load():
    return json.loads(
        (ROOT / "tests/fixtures/sbm_batch/request.json").read_text(encoding="utf-8")
    )


def test_submit_and_duplicate_submission():
    _, gateway = build()
    first = gateway.submit(load())
    second = gateway.submit(load())
    assert first["status"] == "ACCEPTED"
    assert first["duplicate_submission"] is False
    assert second["duplicate_submission"] is True
    assert first["queue_record_id"] == second["queue_record_id"]


def test_status_hides_internal_error_message():
    service, gateway = build()
    accepted = gateway.submit(load())
    status = gateway.status(accepted["queue_record_id"])
    assert status["status"] == "QUEUED"
    assert status["result_ready"] is False
    assert "request_payload" not in status["items"][0]


def test_duplicate_article_rejected():
    payload = load()
    payload["items"][1]["article_id"] = payload["items"][0]["article_id"]
    _, gateway = build()
    with pytest.raises(SbmIntegrationError, match="Duplicate article"):
        gateway.submit(payload)
