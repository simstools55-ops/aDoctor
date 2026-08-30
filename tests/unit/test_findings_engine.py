from pathlib import Path

from src.doctor.events import MedicalRecordEventLog
from src.doctor.findings import FindingsEngine
from src.doctor.knowledge import ClinicalKnowledgeBase


ROOT = Path(__file__).resolve().parents[2]


def engine():
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    return FindingsEngine(ckb, MedicalRecordEventLog({"FINDING_RECORDED"}))


def make_record(low_sample=False):
    return {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "evidence": [
            {
                "evidence_id": "EVD-20260804-120000-ABCDEF",
                "evidence_code": "CTR_BELOW_POSITION_EXPECTATION",
                "created_at": "2026-08-04T12:00:00+00:00",
                "source_observation_ids": ["OBS-1"],
                "measured_values": {"ctr": 0.005},
                "comparison_basis": {"period": "days_28"},
                "rule_version": "1.0",
                "low_sample": low_sample,
                "fingerprint": "a" * 64,
            }
        ],
        "vital_profiles": [
            {
                "profile_id": "VPR-20260804-120100-ABCDEF",
                "signs": [
                    {"code": "CTR_HEALTH", "status": "AVAILABLE", "score": 35, "classification": "TREATMENT_REQUIRED"},
                    {"code": "VISIBILITY", "status": "AVAILABLE", "score": 80, "classification": "MILD_ATTENTION"},
                ]
            }
        ],
        "findings": [],
        "counters": {"finding_count": 0},
        "updated_at": "2026-08-04T12:00:00+00:00",
    }


def test_generates_ctr_and_high_visibility_findings():
    record = make_record()
    created = engine().generate_all(record)
    codes = {item["finding_code"] for item in created}
    assert "CTR_UNDERPERFORMING" in codes
    assert "HIGH_VISIBILITY_LOW_CLICK" in codes
    assert record["counters"]["finding_count"] == 2


def test_low_sample_reduces_confidence_and_adds_info_finding():
    record = make_record(low_sample=True)
    created = engine().generate_all(record)
    ctr = next(x for x in created if x["finding_code"] == "CTR_UNDERPERFORMING")
    assert ctr["confidence"] == 60
    assert any(x["finding_code"] == "INSUFFICIENT_EVIDENCE" for x in created)


def test_duplicate_findings_are_skipped():
    record = make_record()
    e = engine()
    e.generate_all(record)
    before = len(record["findings"])
    second = e.generate_all(record)
    assert second == []
    assert len(record["findings"]) == before
