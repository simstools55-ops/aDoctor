from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.treatment_recommendation import (
    ReferralFactory,
    TreatmentRecommendationEngine,
    TreatmentRecommendationService,
)


ROOT = Path(__file__).resolve().parents[2]


def test_recommendation_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/treatment_recommendation/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/treatment_recommendation/treatment_recommendation_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = TreatmentRecommendationService(
        engine=TreatmentRecommendationEngine(policy),
        referral_factory=ReferralFactory(),
        event_log=MedicalRecordEventLog(
            {"TREATMENT_RECOMMENDATION_CREATED"}
        ),
    )
    first = service.recommend(record, idempotency_key="treatment:1")
    second = service.recommend(record, idempotency_key="treatment:1")

    assert first["recommendation_id"] == second["recommendation_id"]
    assert len(record["treatment_recommendations"]) == 1
    assert record["counters"]["treatment_recommendation_count"] == 1
    assert first["referral_request"]["contract_name"] == "SIMS_DOCTOR_WRITER_REQUEST_V1"
