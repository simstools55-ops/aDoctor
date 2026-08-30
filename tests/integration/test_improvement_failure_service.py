from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.improvement_failure import (
    ImprovementFailureEngine, ImprovementFailureService
)


ROOT = Path(__file__).resolve().parents[2]


def test_assessment_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/improvement_failure/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/improvement_failure/improvement_failure_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = ImprovementFailureService(
        engine=ImprovementFailureEngine(policy),
        event_log=MedicalRecordEventLog({"IMPROVEMENT_FAILURE_ASSESSED"}),
    )
    first = service.assess(record, idempotency_key="failure:1")
    second = service.assess(record, idempotency_key="failure:1")

    assert first["assessment_id"] == second["assessment_id"]
    assert len(record["improvement_failure_assessments"]) == 1
    assert record["counters"]["improvement_failure_assessment_count"] == 1
