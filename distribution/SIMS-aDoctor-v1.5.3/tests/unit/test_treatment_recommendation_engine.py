from pathlib import Path
import json

from src.doctor.treatment_recommendation import TreatmentRecommendationEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/treatment_recommendation/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/treatment_recommendation/treatment_recommendation_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_local_optimization_maps_to_writer():
    record = load()
    composite = record["composite_diagnoses"][-1]
    result = TreatmentRecommendationEngine(policy()).recommend(
        record, composite
    )
    assert result["referral_target"] == "SIMS_WRITER"
    assert result["treatment_mode"] == "LOCAL_OPTIMIZATION"


def test_full_rewrite_is_downgraded_when_blocked():
    record = load()
    composite = record["composite_diagnoses"][-1]
    composite["final_diagnosis"] = "FULL_REWRITE_RECOMMENDED"
    composite["safety"]["full_rewrite_allowed"] = False
    composite["safety"]["winner_query_protected"] = True
    result = TreatmentRecommendationEngine(policy()).recommend(
        record, composite
    )
    assert result["treatment_mode"] == "LOCAL_OPTIMIZATION"
    assert "FULL_REWRITE" in result["prohibited_actions"]


def test_new_article_requires_permission():
    record = load()
    composite = record["composite_diagnoses"][-1]
    composite["final_diagnosis"] = "NEW_ARTICLE_RECOMMENDED"
    composite["safety"]["new_article_allowed"] = False
    result = TreatmentRecommendationEngine(policy()).recommend(
        record, composite
    )
    assert result["referral_target"] == "FOLLOW_UP"


def test_merge_maps_to_merge():
    record = load()
    composite = record["composite_diagnoses"][-1]
    composite["final_diagnosis"] = "MERGE_RECOMMENDED"
    composite["safety"]["merge_required"] = True
    result = TreatmentRecommendationEngine(policy()).recommend(
        record, composite
    )
    assert result["referral_target"] == "SIMS_MERGE"
