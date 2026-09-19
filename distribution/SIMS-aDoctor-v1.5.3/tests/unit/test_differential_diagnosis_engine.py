from pathlib import Path

from src.doctor.differential import DifferentialDiagnosisEngine
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase


ROOT = Path(__file__).resolve().parents[2]


def finding(fid, code, confidence=85, low_sample=False, evidence=("EVD-1",)):
    return {
        "finding_id": fid,
        "finding_code": code,
        "severity": "MODERATE",
        "confidence": confidence,
        "evidence_ids": list(evidence),
        "rationale": {"low_sample": low_sample},
    }


def engine():
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    return DifferentialDiagnosisEngine(ckb, MedicalRecordEventLog({"DIFFERENTIAL_UPDATED"}))


def record(findings):
    return {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "findings": findings,
        "differential_assessments": [],
        "history": [],
        "counters": {"differential_count": 0},
        "updated_at": "2026-08-04T00:00:00+00:00",
    }


def test_ranks_low_ctr_candidate_first():
    item = record([
        finding("FND-1", "CTR_UNDERPERFORMING"),
        finding("FND-2", "HIGH_VISIBILITY_LOW_CLICK"),
    ])
    result = engine().assess(item, idempotency_key="dif:1")
    assert result["top_candidate"] == "LOW_CTR_WITH_STRONG_POSITION"
    assert result["candidates"][0]["rank"] == 1
    assert result["candidates"][0]["confidence"] == 100


def test_long_term_decline_needs_two_supporting_findings():
    item = record([finding("FND-1", "POSITION_DECLINING")])
    result = engine().assess(item, idempotency_key="dif:2")
    assert all(x["diagnosis_code"] != "LONG_TERM_DECLINE" for x in result["candidates"])

    item2 = record([
        finding("FND-1", "POSITION_DECLINING"),
        finding("FND-2", "LOW_VISIBILITY"),
    ])
    result2 = engine().assess(item2, idempotency_key="dif:3")
    assert any(x["diagnosis_code"] == "LONG_TERM_DECLINE" for x in result2["candidates"])


def test_low_sample_penalty_applies():
    item = record([finding("FND-1", "INSUFFICIENT_EVIDENCE", low_sample=True)])
    result = engine().assess(item, idempotency_key="dif:4")
    candidate = result["candidates"][0]
    assert candidate["diagnosis_code"] == "INSUFFICIENT_DATA"
    assert candidate["confidence"] == 80


def test_replay_is_idempotent():
    item = record([finding("FND-1", "CONTENT_OUTDATED")])
    e = engine()
    first = e.assess(item, idempotency_key="dif:5")
    second = e.assess(item, idempotency_key="dif:5")
    assert first["differential_id"] == second["differential_id"]
    assert len(item["differential_assessments"]) == 1
    assert len(item["events"]) == 1
