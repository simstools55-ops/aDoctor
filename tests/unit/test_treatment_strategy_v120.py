from pathlib import Path
import json

from src.doctor.treatment_recommendation import TreatmentRecommendationEngine

ROOT = Path(__file__).resolve().parents[2]


def _engine():
    policy = json.loads((ROOT / "knowledge/treatment_recommendation/treatment_recommendation_policy_v1.json").read_text(encoding="utf-8"))
    return TreatmentRecommendationEngine(policy)


def test_algorithm_rollout_can_defer_rewrite_to_wait():
    composite = {
        "composite_diagnosis_id": "CDX-1",
        "final_diagnosis": "LOCAL_OPTIMIZATION",
        "priority": 70,
        "reasons": [],
        "safety": {
            "new_article_allowed": False,
            "full_rewrite_allowed": True,
            "winner_query_protected": False,
            "merge_required": False,
            "algorithm_wait_recommended": True,
        },
        "algorithm_assessment": {
            "status": "HIGH",
            "update": {"rollout_status": "IN_PROGRESS"},
        },
        "supporting_assessments": [],
    }
    result = _engine().recommend({}, composite)
    assert result["strategy"] == "WAIT"
    assert result["referral_target"] == "OBSERVE"
    assert result["wait_plan"]["recommended_review_days"] == 14
    assert result["user_todo"][0]["action"] == "WAIT"


def test_severe_rewrite_without_algorithm_wait_remains_full_rewrite():
    composite = {
        "composite_diagnosis_id": "CDX-2",
        "final_diagnosis": "FULL_REWRITE_RECOMMENDED",
        "priority": 90,
        "reasons": [],
        "safety": {
            "new_article_allowed": False,
            "full_rewrite_allowed": True,
            "winner_query_protected": False,
            "merge_required": False,
            "algorithm_wait_recommended": False,
        },
        "algorithm_assessment": {"status": "LOW", "update": {"rollout_status": "COMPLETED"}},
        "supporting_assessments": [],
    }
    result = _engine().recommend({}, composite)
    assert result["strategy"] == "FULL_REWRITE"
    assert result["referral_target"] == "SIMS_WRITER"
