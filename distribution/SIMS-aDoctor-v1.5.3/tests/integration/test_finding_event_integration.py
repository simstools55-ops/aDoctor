from pathlib import Path

from src.doctor.events import MedicalRecordEventLog
from src.doctor.findings import FindingsEngine
from src.doctor.knowledge import ClinicalKnowledgeBase


ROOT = Path(__file__).resolve().parents[2]


def test_finding_is_persisted_with_event():
    record = {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "evidence": [{
            "evidence_id": "EVD-20260804-120000-ABCDEF",
            "evidence_code": "LONG_TIME_SINCE_UPDATE",
            "created_at": "2026-08-04T12:00:00+00:00",
            "source_observation_ids": ["OBS-1"],
            "measured_values": {"days_since_update": 500},
            "comparison_basis": {"minimum_days_since_update": 365},
            "rule_version": "1.0",
            "low_sample": False,
            "fingerprint": "b" * 64,
        }],
        "vital_profiles": [{
            "profile_id": "VPR-20260804-120100-ABCDEF",
            "signs": [{
                "code": "FRESHNESS",
                "status": "AVAILABLE",
                "score": 35,
                "classification": "TREATMENT_REQUIRED",
            }]
        }],
        "findings": [],
        "counters": {"finding_count": 0},
        "updated_at": "2026-08-04T12:00:00+00:00",
    }
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    engine = FindingsEngine(ckb, MedicalRecordEventLog({"FINDING_RECORDED"}))
    created = engine.generate_all(record)

    assert created[0]["finding_code"] == "CONTENT_OUTDATED"
    assert record["events"][0]["event_type"] == "FINDING_RECORDED"
    assert record["events"][0]["payload"]["finding"]["finding_id"] == created[0]["finding_id"]
