from pathlib import Path

from src.doctor.differential import DifferentialDiagnosisEngine
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase


ROOT = Path(__file__).resolve().parents[2]


def test_differential_assessment_is_recorded_with_event():
    record = {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "findings": [{
            "finding_id": "FND-1",
            "finding_code": "CONTENT_OUTDATED",
            "severity": "MODERATE",
            "confidence": 80,
            "evidence_ids": ["EVD-1"],
            "rationale": {"low_sample": False},
        }],
        "differential_assessments": [],
        "history": [],
        "counters": {"differential_count": 0},
        "updated_at": "2026-08-04T00:00:00+00:00",
    }
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    engine = DifferentialDiagnosisEngine(
        ckb, MedicalRecordEventLog({"DIFFERENTIAL_UPDATED"})
    )
    result = engine.assess(record, idempotency_key="dif:integration")

    assert result["top_candidate"] == "CONTENT_STALE"
    assert record["events"][0]["event_type"] == "DIFFERENTIAL_UPDATED"
    assert record["counters"]["differential_count"] == 1
    assert record["case_status"] == "DIAGNOSING"
