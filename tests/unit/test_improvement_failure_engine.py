from pathlib import Path
import json

from src.doctor.improvement_failure import ImprovementFailureEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/improvement_failure/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/improvement_failure/improvement_failure_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_detects_wrong_treatment_direction():
    result = ImprovementFailureEngine(policy()).assess(load())
    assert result["classification"] == "POSSIBLE_WRONG_TREATMENT_DIRECTION"
    assert result["severity"] == "SEVERE"
    assert result["metrics"]["vital_score_change"] == -13


def test_low_sample_is_not_confirmed_failure():
    record = load()
    record["observations"][0]["facts"]["assessment"]["low_sample"] = True
    result = ImprovementFailureEngine(policy()).assess(record)
    assert result["classification"] == "INSUFFICIENT_FOLLOW_UP"


def test_recurrent_failure_has_priority():
    record = load()
    record["final_diagnoses"] = [
        {
            "status": "CONFIRMED",
            "diagnosis_code": "IMPROVEMENT_FAILURE"
        },
        {
            "status": "CONFIRMED",
            "diagnosis_code": "POST_IMPROVEMENT_WORSENING"
        }
    ]
    result = ImprovementFailureEngine(policy()).assess(record)
    assert result["classification"] == "RECURRENT_FAILURE"
    assert result["metrics"]["failure_recurrence_count"] == 2


def test_no_effect_is_distinguished():
    record = load()
    assessment = record["observations"][0]["facts"]["assessment"]
    assessment["effect_score"] = 0.01
    assessment["metric_changes"] = {
        "clicks": 0.01, "impressions": -0.01,
        "ctr": 0.0, "position": 0.0
    }
    record["vital_scores"][-1]["overall_score"] = 67
    result = ImprovementFailureEngine(policy()).assess(record)
    assert result["classification"] == "NO_MEASURABLE_EFFECT"
