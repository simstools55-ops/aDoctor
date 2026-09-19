from pathlib import Path
import json

from src.doctor.diagnosis import FinalDiagnosisEngine
from src.doctor.differential import DifferentialDiagnosisEngine
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.referral import ReferralEngine
from src.doctor.treatment import TreatmentRecommendationEngine
from src.doctor.treatment_history import (
    TreatmentHistoryInput, TreatmentHistoryObservationService,
    TreatmentHistoryEvidenceEngine, TreatmentHistoryFindingsEngine
)


ROOT = Path(__file__).resolve().parents[2]


def test_post_improvement_worsening_routes_to_writer():
    raw = json.loads(
        (ROOT / "tests/fixtures/treatment_history/worsened.json")
        .read_text(encoding="utf-8")
    )
    parsed = TreatmentHistoryInput.from_dict(raw)
    record = {
        "case_id": "CASE-1",
        "medical_record_id": "MR-1",
        "patient": {
            "site_id": "site",
            "article_id": "A1",
            "article_url": "https://example.com/a1",
            "article_title": "Article",
        },
        "events": [], "observations": [], "evidence": [], "findings": [],
        "vital_profiles": [], "differential_assessments": [],
        "final_diagnoses": [], "treatment_recommendations": [],
        "referrals": [], "history": [],
        "counters": {
            "observation_count": 0, "evidence_count": 0, "finding_count": 0,
            "differential_count": 0, "final_diagnosis_count": 0,
            "treatment_recommendation_count": 0, "referral_count": 0
        },
    }
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    allowed = {
        "OBSERVATION_RECORDED", "EVIDENCE_RECORDED", "FINDING_RECORDED",
        "DIFFERENTIAL_UPDATED", "FINAL_DIAGNOSIS_CONFIRMED",
        "TREATMENT_RECOMMENDED", "REFERRAL_ISSUED"
    }
    log = MedicalRecordEventLog(allowed)
    TreatmentHistoryObservationService(log).record(
        record, parsed, idempotency_key="history:obs"
    )
    TreatmentHistoryEvidenceEngine(log).extract(record)
    TreatmentHistoryFindingsEngine(log).generate(record)
    DifferentialDiagnosisEngine(ckb, log).assess(
        record, idempotency_key="history:dif"
    )
    diagnosis = FinalDiagnosisEngine(ckb, log).confirm(
        record, idempotency_key="history:dx"
    )
    treatment = TreatmentRecommendationEngine(ckb, log).recommend(
        record, idempotency_key="history:tr"
    )
    referral = ReferralEngine(ckb, log).issue(
        record, idempotency_key="history:ref"
    )

    assert diagnosis["diagnosis_code"] == "POST_IMPROVEMENT_WORSENING"
    assert treatment["treatment_code"] == "REVIEW_AND_ROLLBACK_WORSENING"
    assert treatment["target"] == "WRITER"
    assert referral["target"] == "WRITER"
