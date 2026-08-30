from pathlib import Path
import json

from src.doctor.cross_article import CrossArticleObservationInput, CrossArticleObservationService, CrossArticleFindingsEngine
from src.doctor.diagnosis import FinalDiagnosisEngine
from src.doctor.differential import DifferentialDiagnosisEngine
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.referral import ReferralEngine
from src.doctor.treatment import TreatmentRecommendationEngine


ROOT = Path(__file__).resolve().parents[2]


def test_merge_candidate_routes_to_merge():
    raw = json.loads(
        (ROOT / "tests/fixtures/cross_article/merge_candidate.json")
        .read_text(encoding="utf-8")
    )
    parsed = CrossArticleObservationInput.from_dict(raw)
    record = {
        "case_id": "CASE-1",
        "medical_record_id": "MR-1",
        "patient": {
            "site_id": "site",
            "article_id": "A1",
            "article_url": "https://example.com/a1",
            "article_title": "Windows 11 Wi-Fi設定方法",
        },
        "events": [],
        "observations": [],
        "findings": [],
        "evidence": [],
        "vital_profiles": [],
        "differential_assessments": [],
        "final_diagnoses": [],
        "treatment_recommendations": [],
        "referrals": [],
        "history": [],
        "counters": {
            "observation_count": 0, "finding_count": 0,
            "differential_count": 0, "final_diagnosis_count": 0,
            "treatment_recommendation_count": 0, "referral_count": 0
        },
    }
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    allowed = {
        "OBSERVATION_RECORDED", "FINDING_RECORDED", "DIFFERENTIAL_UPDATED",
        "FINAL_DIAGNOSIS_CONFIRMED", "TREATMENT_RECOMMENDED", "REFERRAL_ISSUED"
    }
    log = MedicalRecordEventLog(allowed)
    CrossArticleObservationService(log).record(record, parsed, idempotency_key="cross:1")
    CrossArticleFindingsEngine(log, ckb.cross_article_finding_rules()).generate(record)
    DifferentialDiagnosisEngine(ckb, log).assess(record, idempotency_key="dif:cross")
    diagnosis = FinalDiagnosisEngine(ckb, log).confirm(record, idempotency_key="dx:cross")
    treatment = TreatmentRecommendationEngine(ckb, log).recommend(record, idempotency_key="tr:cross")
    referral = ReferralEngine(ckb, log).issue(record, idempotency_key="ref:cross")

    assert diagnosis["diagnosis_code"] == "ARTICLE_MERGE_REQUIRED"
    assert treatment["target"] == "MERGE"
    assert referral["target"] == "MERGE"
