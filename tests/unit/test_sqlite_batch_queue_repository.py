from src.doctor.batch.queue import SQLiteBatchQueueRepository


def record(queue_id="BQ-1", status="QUEUED"):
    return {
        "queue_record_id": queue_id,
        "batch_request_id": f"REQUEST-{queue_id}",
        "status": status,
        "updated_at": "2026-08-04T00:00:00+00:00",
        "items": [],
    }


def test_sqlite_repository_persists_across_instances(tmp_path):
    path = tmp_path / "queue.db"
    first = SQLiteBatchQueueRepository(path)
    first.create(record())
    second = SQLiteBatchQueueRepository(path)
    assert second.get("BQ-1")["batch_request_id"] == "REQUEST-BQ-1"
    assert second.count() == 1


def test_sqlite_repository_updates_and_lists_incomplete(tmp_path):
    repository = SQLiteBatchQueueRepository(tmp_path / "queue.db")
    item = repository.create(record())
    item["status"] = "RUNNING"
    item["updated_at"] = "2026-08-04T01:00:00+00:00"
    repository.save(item)
    assert repository.get("BQ-1")["status"] == "RUNNING"
    assert len(repository.list_incomplete()) == 1
    item["status"] = "COMPLETED"
    repository.save(item)
    assert repository.list_incomplete() == []
