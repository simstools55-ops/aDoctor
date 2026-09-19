from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.long_term_degradation import (
    LongTermDegradationEngine, LongTermDegradationService
)


ROOT = Path(__file__).resolve().parents[2]


def test_assessment_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/long_term_degradation/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/long_term_degradation/long_term_degradation_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = LongTermDegradationService(
        engine=LongTermDegradationEngine(policy),
        event_log=MedicalRecordEventLog({"LONG_TERM_DEGRADATION_ASSESSED"}),
    )
    first = service.assess(record, idempotency_key="long:1")
    second = service.assess(record, idempotency_key="long:1")

    assert first["assessment_id"] == second["assessment_id"]
    assert len(record["long_term_degradation_assessments"]) == 1
    assert record["counters"]["long_term_degradation_assessment_count"] == 1
