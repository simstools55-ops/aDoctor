from pathlib import Path
import json

from src.doctor.batch import BatchPriorityCalculator
from src.doctor.batch.queue import BatchQueueService, InMemoryBatchQueueRepository
from src.doctor.integration.sbm import SbmBatchGateway, SQLiteSbmImportLedger


ROOT = Path(__file__).resolve().parents[2]


def test_terminal_batch_exports_and_import_ack_is_idempotent(tmp_path):
    queue_policy = json.loads(
        (ROOT / "knowledge/batch/batch_queue_policy_v1.json").read_text(encoding="utf-8")
    )
    batch_policy = json.loads(
        (ROOT / "knowledge/batch/batch_policy_v1.json").read_text(encoding="utf-8")
    )
    repository = InMemoryBatchQueueRepository()
    service = BatchQueueService(
        repository=repository,
        policy=queue_policy,
        priority_calculator=BatchPriorityCalculator(batch_policy),
    )
    gateway = SbmBatchGateway(service)
    payload = json.loads(
        (ROOT / "tests/fixtures/sbm_batch/request.json").read_text(encoding="utf-8")
    )
    accepted = gateway.submit(payload)
    queue_id = accepted["queue_record_id"]
    record = repository.get(queue_id)
    for index, item in enumerate(record["items"], start=1):
        item["status"] = "COMPLETED"
        item["case_id"] = f"CASE-{index}"
        item["result"] = {
            "single_case_result": {
                "contract_name": "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1",
                "contract_version": "1.0",
                "result_status": "DIAGNOSED",
                "referral": {"target": "WRITER"},
            },
            "writer_request": {
                "contract_name": "SIMS_DOCTOR_WRITER_REQUEST_V1",
                "contract_version": "1.0",
            },
        }
    record["status"] = "COMPLETED"
    record["progress"] = {
        "total": 2, "completed": 2, "failed": 0,
        "pending": 0, "running": 0, "skipped": 0
    }
    repository.save(record)

    status = gateway.status(queue_id)
    assert status["result_ready"] is True

    package = gateway.export_result(queue_id)
    assert package["summary"]["completed"] == 2
    assert package["summary"]["writer_requests"] == 2

    ledger = SQLiteSbmImportLedger(tmp_path / "imports.db")
    first = ledger.acknowledge(package, imported_items=2)
    second = ledger.acknowledge(package, imported_items=2)
    assert first["status"] == "IMPORTED"
    assert second["status"] == "ALREADY_IMPORTED"
