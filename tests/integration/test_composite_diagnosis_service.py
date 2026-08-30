from pathlib import Path
import json

from src.doctor.composite_diagnosis import (
    CompositeDiagnosisEngine, CompositeDiagnosisService
)
from src.doctor.events import MedicalRecordEventLog


ROOT = Path(__file__).resolve().parents[2]


def test_composite_diagnosis_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/composite_diagnosis/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/composite_diagnosis/composite_diagnosis_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = CompositeDiagnosisService(
        engine=CompositeDiagnosisEngine(policy),
        event_log=MedicalRecordEventLog({"COMPOSITE_DIAGNOSIS_COMPLETED"}),
    )
    first = service.diagnose(record, idempotency_key="composite:1")
    second = service.diagnose(record, idempotency_key="composite:1")

    assert first["composite_diagnosis_id"] == second["composite_diagnosis_id"]
    assert len(record["composite_diagnoses"]) == 1
    assert record["counters"]["composite_diagnosis_count"] == 1
