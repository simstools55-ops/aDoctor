from pathlib import Path

import pytest

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.referral import ReferralEngine, ReferralError
from src.doctor.treatment import TreatmentRecommendationEngine


ROOT = Path(__file__).resolve().parents[2]


def engines():
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    log = MedicalRecordEventLog({"TREATMENT_RECOMMENDED", "REFERRAL_ISSUED"})
    return TreatmentRecommendationEngine(ckb, log), ReferralEngine(ckb, log)


def record(status="CONFIRMED", diagnosis_code="CONTENT_STALE", defer_reason=None):
    return {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "patient": {
            "site_id": "site",
            "article_id": "A000001",
            "article_url": "https://example.com/a",
            "article_title": "Article",
        },
        "events": [],
        "final_diagnoses": [{
            "diagnosis_id": "DX-1",
            "status": status,
            "diagnosis_code": diagnosis_code,
            "confidence": 90,
            "severity": "MODERATE",
            "defer_reason": defer_reason,
            "supporting_finding_ids": ["FND-1"],
            "evidence_ids": ["EVD-1"],
        }],
        "treatment_recommendations": [],
        "referrals": [],
        "counters": {"treatment_recommendation_count": 0, "referral_count": 0},
    }


def test_confirmed_content_stale_routes_to_writer():
    treatment, referral = engines()
    item = record()
    tr = treatment.recommend(item, idempotency_key="tr:1")
    ref = referral.issue(item, idempotency_key="ref:1")
    assert tr["target"] == "WRITER"
    assert ref["target"] == "WRITER"
    assert item["case_status"] == "REFERRED"


def test_deferred_routes_to_observation():
    treatment, referral = engines()
    item = record(status="DEFERRED", diagnosis_code=None, defer_reason="LOW_SAMPLE_ONLY")
    tr = treatment.recommend(item, idempotency_key="tr:2")
    ref = referral.issue(item, idempotency_key="ref:2")
    assert tr["target"] == "OBSERVATION"
    assert ref["target"] == "OBSERVATION"
    assert item["case_status"] == "FOLLOW_UP"


def test_replay_is_idempotent():
    treatment, referral = engines()
    item = record()
    a = treatment.recommend(item, idempotency_key="tr:3")
    b = treatment.recommend(item, idempotency_key="tr:3")
    assert a["treatment_recommendation_id"] == b["treatment_recommendation_id"]
    referral.issue(item, idempotency_key="ref:3")
    referral.issue(item, idempotency_key="ref:3")
    assert len(item["treatment_recommendations"]) == 1
    assert len(item["referrals"]) == 1
