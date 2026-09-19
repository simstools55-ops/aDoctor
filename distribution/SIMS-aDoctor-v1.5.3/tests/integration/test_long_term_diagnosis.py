from pathlib import Path
import json

from src.doctor.diagnosis import FinalDiagnosisEngine
from src.doctor.differential import DifferentialDiagnosisEngine
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.long_term import (
    LongTermObservationInput, LongTermObservationService,
    LongTermEvidenceEngine, LongTermFindingsEngine
)
from src.doctor.referral import ReferralEngine
from src.doctor.treatment import TreatmentRecommendationEngine


ROOT = Path(__file__).resolve().parents[2]


def test_long_term_decline_routes_to_writer():
    raw = json.loads(
        (ROOT / "tests/fixtures/long_term/gradual_decline.json")
        .read_text(encoding="utf-8")
    )
    parsed = LongTermObservationInput.from_dict(raw)
    record = {
        "case_id": "CASE-1",
        "medical_record_id": "MR-1",
        "patient": {
            "site_id": "site",
            "article_id": "A1",
            "article_url": "https://example.com/a1",
            "article_title": "Article",
        },
        "events": [],
        "observations": [],
        "evidence": [],
        "findings": [],
        "vital_profiles": [],
        "differential_assessments": [],
        "final_diagnoses": [],
        "treatment_recommendations": [],
        "referrals": [],
        "history": [],
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
    LongTermObservationService(log).record(record, parsed, idempotency_key="lt:obs")
    LongTermEvidenceEngine(log).extract(record)
    LongTermFindingsEngine(log).generate(record)
    DifferentialDiagnosisEngine(ckb, log).assess(record, idempotency_key="lt:dif")
    diagnosis = FinalDiagnosisEngine(ckb, log).confirm(record, idempotency_key="lt:dx")
    treatment = TreatmentRecommendationEngine(ckb, log).recommend(record, idempotency_key="lt:tr")
    referral = ReferralEngine(ckb, log).issue(record, idempotency_key="lt:ref")

    assert diagnosis["diagnosis_code"] == "LONG_TERM_DECAY"
    assert treatment["target"] == "WRITER"
    assert referral["target"] == "WRITER"
