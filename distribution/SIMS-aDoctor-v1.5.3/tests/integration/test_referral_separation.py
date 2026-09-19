from pathlib import Path

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.referral import ReferralEngine
from src.doctor.treatment import TreatmentRecommendationEngine


ROOT = Path(__file__).resolve().parents[2]


def test_diagnosis_and_referral_remain_separate_records():
    record = {
        "case_id": "CASE-1",
        "medical_record_id": "MR-1",
        "patient": {
            "site_id": "site",
            "article_id": "A1",
            "article_url": "https://example.com/a",
            "article_title": "Article",
        },
        "events": [],
        "final_diagnoses": [{
            "diagnosis_id": "DX-1",
            "status": "CONFIRMED",
            "diagnosis_code": "CTR_PROBLEM",
            "confidence": 95,
            "severity": "SEVERE",
            "defer_reason": None,
            "supporting_finding_ids": ["F1"],
            "evidence_ids": ["E1"],
        }],
        "treatment_recommendations": [],
        "referrals": [],
        "counters": {"treatment_recommendation_count": 0, "referral_count": 0},
    }
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    log = MedicalRecordEventLog({"TREATMENT_RECOMMENDED", "REFERRAL_ISSUED"})
    TreatmentRecommendationEngine(ckb, log).recommend(record, idempotency_key="tr")
    ReferralEngine(ckb, log).issue(record, idempotency_key="ref")

    assert "target" not in record["final_diagnoses"][0]
    assert record["referrals"][0]["diagnosis_id"] == "DX-1"
    assert [e["event_type"] for e in record["events"]] == [
        "TREATMENT_RECOMMENDED", "REFERRAL_ISSUED"
    ]
