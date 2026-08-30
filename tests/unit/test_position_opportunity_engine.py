from pathlib import Path
import json

from src.doctor.position_opportunity import PositionOpportunityEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/position_opportunity/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/position_opportunity/position_opportunity_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_detects_high_position_opportunity():
    result = PositionOpportunityEngine(policy()).assess(load())
    assert result["classification"] == "HIGH_POSITION_OPPORTUNITY"
    assert result["metrics"]["position"] == 12.4
    assert result["protections"]["new_article_allowed"] is False


def test_winner_query_is_protected():
    record = load()
    record["observations"][0]["facts"]["queries"] = [
        {"query": "winner", "clicks": 14, "impressions": 1000},
        {"query": "other", "clicks": 4, "impressions": 900}
    ]
    result = PositionOpportunityEngine(policy()).assess(record)
    assert result["classification"] == "WINNER_QUERY_PROTECTED"


def test_low_visibility_is_detected():
    record = load()
    record["observations"][0]["facts"]["metrics"]["position"] = 42.0
    result = PositionOpportunityEngine(policy()).assess(record)
    assert result["classification"] == "LOW_VISIBILITY_OR_MISALIGNMENT"


def test_low_sample_is_insufficient():
    record = load()
    record["observations"][0]["facts"]["metrics"]["low_sample"] = True
    result = PositionOpportunityEngine(policy()).assess(record)
    assert result["classification"] == "INSUFFICIENT_DATA"
