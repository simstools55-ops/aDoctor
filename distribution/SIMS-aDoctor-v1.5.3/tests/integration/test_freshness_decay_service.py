from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.freshness_decay import FreshnessDecayEngine, FreshnessDecayService


ROOT = Path(__file__).resolve().parents[2]


def test_assessment_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/freshness_decay/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/freshness_decay/freshness_decay_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = FreshnessDecayService(
        engine=FreshnessDecayEngine(policy),
        event_log=MedicalRecordEventLog({"FRESHNESS_DECAY_ASSESSED"}),
    )
    first = service.assess(record, idempotency_key="fresh:1")
    second = service.assess(record, idempotency_key="fresh:1")

    assert first["assessment_id"] == second["assessment_id"]
    assert len(record["freshness_decay_assessments"]) == 1
    assert record["counters"]["freshness_decay_assessment_count"] == 1
