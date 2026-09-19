from pathlib import Path
import json

from src.doctor.vital_score import VitalScoreEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/vital_score/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/vital_score/vital_score_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_calculates_overall_score():
    result = VitalScoreEngine(policy()).calculate(load())
    assert result["score_status"] == "CALCULATED"
    assert 0 <= result["overall_score"] <= 100
    assert result["health_band"] in {
        "EXCELLENT", "GOOD", "WATCH", "UNHEALTHY", "CRITICAL"
    }
    assert len(result["components"]) == 7


def test_missing_signs_are_reweighted():
    record = load()
    record["vital_profiles"][0]["signs"] = record["vital_profiles"][0]["signs"][:4]
    result = VitalScoreEngine(policy()).calculate(record)
    assert result["score_status"] == "CALCULATED"
    assert len(result["missing_signs"]) == 3
    total_effective_weight = sum(
        item["effective_weight"] for item in result["components"]
    )
    assert abs(total_effective_weight - 1.0) < 0.00001


def test_insufficient_signs_returns_no_score():
    record = load()
    record["vital_profiles"][0]["signs"] = record["vital_profiles"][0]["signs"][:2]
    result = VitalScoreEngine(policy()).calculate(record)
    assert result["score_status"] == "INSUFFICIENT_DATA"
    assert result["overall_score"] is None


def test_low_sample_penalty_applies():
    record = load()
    record["vital_profiles"][0]["signs"][0]["low_sample"] = True
    result = VitalScoreEngine(policy()).calculate(record)
    assert result["adjustments"]["penalty"] >= 8
