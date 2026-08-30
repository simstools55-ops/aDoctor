from pathlib import Path
import json

from src.doctor.long_term_degradation import LongTermDegradationEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/long_term_degradation/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/long_term_degradation/long_term_degradation_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_detects_sharp_degradation():
    result = LongTermDegradationEngine(policy()).assess(load())
    assert result["classification"] == "SHARP_DEGRADATION"
    assert result["severity"] == "CRITICAL"
    assert result["metrics"]["vital_score_change"] == -14


def test_seasonality_blocks_degradation():
    record = load()
    trend = record["observations"][0]["facts"]["trend"]
    trend["visibility_change_ratio"] = -0.20
    trend["seasonality_score"] = 0.90
    result = LongTermDegradationEngine(policy()).assess(record)
    assert result["classification"] == "SEASONAL_VARIATION"


def test_recovery_has_priority():
    record = load()
    trend = record["observations"][0]["facts"]["trend"]
    trend["classification"] = "RECOVERY"
    trend["visibility_change_ratio"] = 0.30
    result = LongTermDegradationEngine(policy()).assess(record)
    assert result["classification"] == "RECOVERY_IN_PROGRESS"


def test_low_sample_reduces_confidence():
    record = load()
    record["observations"][0]["facts"]["trend"]["low_sample"] = True
    result = LongTermDegradationEngine(policy()).assess(record)
    assert result["confidence"] < 90
