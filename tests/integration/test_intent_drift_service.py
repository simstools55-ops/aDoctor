from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.intent_drift import IntentDriftEngine, IntentDriftService


ROOT = Path(__file__).resolve().parents[2]


def test_assessment_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/intent_drift/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/intent_drift/intent_drift_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = IntentDriftService(
        engine=IntentDriftEngine(policy),
        event_log=MedicalRecordEventLog({"INTENT_DRIFT_ASSESSED"}),
    )
    first = service.assess(record, idempotency_key="intent:1")
    second = service.assess(record, idempotency_key="intent:1")

    assert first["assessment_id"] == second["assessment_id"]
    assert len(record["intent_drift_assessments"]) == 1
    assert record["counters"]["intent_drift_assessment_count"] == 1
