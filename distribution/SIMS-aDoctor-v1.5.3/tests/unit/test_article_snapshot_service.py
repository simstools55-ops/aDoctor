from pathlib import Path
import json

from src.doctor.article_snapshot import ArticleSnapshotInput, ArticleSnapshotService
from src.doctor.events import MedicalRecordEventLog


ROOT = Path(__file__).resolve().parents[2]


def record():
    return {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "patient": {
            "site_id": "sample-site",
            "article_id": "A000001",
            "article_url": "https://example.invalid/entry/example",
        },
        "events": [],
        "observations": [],
        "counters": {"observation_count": 0},
        "case_status": "READY_FOR_OBSERVATION",
    }


def input_data():
    return ArticleSnapshotInput.from_dict(json.loads(
        (ROOT / "tests/fixtures/article_snapshot/complete_snapshot.json")
        .read_text(encoding="utf-8")
    ))


def test_records_snapshot():
    item = record()
    service = ArticleSnapshotService(MedicalRecordEventLog({"OBSERVATION_RECORDED"}))
    result = service.record(item, input_data(), idempotency_key="article:1")
    assert result["observation_type"] == "ARTICLE_SNAPSHOT"
    assert item["counters"]["observation_count"] == 1


def test_replay_is_idempotent():
    item = record()
    service = ArticleSnapshotService(MedicalRecordEventLog({"OBSERVATION_RECORDED"}))
    first = service.record(item, input_data(), idempotency_key="article:2")
    second = service.record(item, input_data(), idempotency_key="article:2")
    assert first["observation_id"] == second["observation_id"]
    assert len(item["observations"]) == 1
