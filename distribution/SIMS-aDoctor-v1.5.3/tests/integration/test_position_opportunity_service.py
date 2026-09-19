from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.position_opportunity import (
    PositionOpportunityEngine, PositionOpportunityService
)


ROOT = Path(__file__).resolve().parents[2]


def test_assessment_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/position_opportunity/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/position_opportunity/position_opportunity_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = PositionOpportunityService(
        engine=PositionOpportunityEngine(policy),
        event_log=MedicalRecordEventLog({"POSITION_OPPORTUNITY_ASSESSED"}),
    )
    first = service.assess(record, idempotency_key="position:1")
    second = service.assess(record, idempotency_key="position:1")

    assert first["assessment_id"] == second["assessment_id"]
    assert len(record["position_opportunity_assessments"]) == 1
    assert record["counters"]["position_opportunity_assessment_count"] == 1
