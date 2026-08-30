from pathlib import Path
import json

from src.doctor.intent_drift import IntentDriftEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/intent_drift/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/intent_drift/intent_drift_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_detects_topic_dispersion():
    result = IntentDriftEngine(policy()).assess(load())
    assert result["classification"] == "TOPIC_DISPERSION"
    assert result["protections"]["new_article_allowed"] is False


def test_winner_query_is_protected():
    record = load()
    queries = record["observations"][0]["facts"]["queries"]
    queries[0]["clicks"] = 25
    for item in queries[1:]:
        item["clicks"] = 1
    result = IntentDriftEngine(policy()).assess(record)
    assert result["classification"] == "WINNER_QUERY_PROTECTED"


def test_emerging_intent_transition():
    record = load()
    record["observations"][0]["facts"]["intent_history"] = [
        {"shares": {"SPEED": 0.20, "CONNECTION": 0.60}},
        {"shares": {"SPEED": 0.50, "CONNECTION": 0.30}},
    ]
    result = IntentDriftEngine(policy()).assess(record)
    assert result["classification"] == "EMERGING_INTENT_TRANSITION"


def test_low_sample_is_insufficient():
    record = load()
    record["observations"][0]["facts"]["metrics"]["low_sample"] = True
    result = IntentDriftEngine(policy()).assess(record)
    assert result["classification"] == "INSUFFICIENT_DATA"
