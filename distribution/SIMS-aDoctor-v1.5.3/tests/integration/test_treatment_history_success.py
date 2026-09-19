import json
from pathlib import Path

from src.doctor.diagnosis import FinalDiagnosisEngine
from src.doctor.differential import DifferentialDiagnosisEngine
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.referral import ReferralEngine
from src.doctor.treatment import TreatmentRecommendationEngine
from src.doctor.treatment_history import (
    TreatmentHistoryAnalyzer, TreatmentHistoryInput,
    TreatmentHistoryObservationService, TreatmentHistoryEvidenceEngine,
    TreatmentHistoryFindingsEngine
)


ROOT = Path(__file__).resolve().parents[2]


def test_success_routes_to_observation():
    policy = json.loads(
        (ROOT / "knowledge/observation/treatment_history/treatment_history_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    baseline = {
        "start_date": "2026-06-01", "end_date": "2026-06-28",
        "clicks": 50, "impressions": 2000, "ctr": 0.025, "position": 9.0
    }
    checkpoints = [{
        "days_after_treatment": 28,
        "start_date": "2026-07-01", "end_date": "2026-07-28",
        "clicks": 80, "impressions": 2600, "ctr": 0.0308, "position": 6.5
    }]
    raw = {
        "contract_name": "SIMS_DOCTOR_TREATMENT_HISTORY_INPUT_V1",
        "contract_version": "1.0",
        "case_id": "CASE-1",
        "article": {
            "site_id": "site", "article_id": "A1",
            "url": "https://example.com/a1"
        },
        "treatment": {
            "treatment_id": "TRT-1",
            "completed_at": "2026-06-30T00:00:00+09:00",
            "treatment_type": "WRITER_REWRITE",
            "changed_fields": ["title"]
        },
        "baseline": baseline,
        "checkpoints": checkpoints,
        "observed_at": "2026-07-29T00:00:00+09:00",
        "assessment": TreatmentHistoryAnalyzer(policy).analyze(
            baseline=baseline, checkpoints=checkpoints
        )
    }
    parsed = TreatmentHistoryInput.from_dict(raw)
    record = {
        "case_id": "CASE-1", "medical_record_id": "MR-1",
        "patient": {
            "site_id": "site", "article_id": "A1",
            "article_url": "https://example.com/a1", "article_title": "Article"
        },
        "events": [], "observations": [], "evidence": [], "findings": [],
        "vital_profiles": [], "differential_assessments": [],
        "final_diagnoses": [], "treatment_recommendations": [],
        "referrals": [], "history": [],
        "counters": {
            "observation_count": 0, "evidence_count": 0, "finding_count": 0,
            "differential_count": 0, "final_diagnosis_count": 0,
            "treatment_recommendation_count": 0, "referral_count": 0
        }
    }
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    allowed = {
        "OBSERVATION_RECORDED", "EVIDENCE_RECORDED", "FINDING_RECORDED",
        "DIFFERENTIAL_UPDATED", "FINAL_DIAGNOSIS_CONFIRMED",
        "TREATMENT_RECOMMENDED", "REFERRAL_ISSUED"
    }
    log = MedicalRecordEventLog(allowed)
    TreatmentHistoryObservationService(log).record(
        record, parsed, idempotency_key="s:obs"
    )
    TreatmentHistoryEvidenceEngine(log).extract(record)
    TreatmentHistoryFindingsEngine(log).generate(record)
    DifferentialDiagnosisEngine(ckb, log).assess(
        record, idempotency_key="s:dif"
    )
    diagnosis = FinalDiagnosisEngine(ckb, log).confirm(
        record, idempotency_key="s:dx"
    )
    treatment = TreatmentRecommendationEngine(ckb, log).recommend(
        record, idempotency_key="s:tr"
    )
    referral = ReferralEngine(ckb, log).issue(
        record, idempotency_key="s:ref"
    )

    assert diagnosis["diagnosis_code"] == "TREATMENT_SUCCESS"
    assert treatment["target"] == "OBSERVATION"
    assert referral["target"] == "OBSERVATION"
