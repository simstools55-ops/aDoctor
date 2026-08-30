from pathlib import Path
import json
from datetime import datetime, timezone

from src.doctor.freshness_decay import FreshnessDecayEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/freshness_decay/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/freshness_decay/freshness_decay_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_detects_severe_freshness_decay():
    result = FreshnessDecayEngine(policy()).assess(load())
    assert result["classification"] == "SEVERE_FRESHNESS_DECAY"
    assert result["protections"]["preferred_scope"] == "BROAD_REFRESH"


def test_recent_update_requires_observation():
    record = load()
    record["patient"]["article_updated_at"] = datetime.now(timezone.utc).isoformat()
    result = FreshnessDecayEngine(policy()).assess(record)
    assert result["classification"] == "RECENT_UPDATE_OBSERVATION"


def test_winner_query_is_protected():
    record = load()
    record["findings"] = record["findings"][:2]
    queries = record["observations"][0]["facts"]["queries"]
    queries[0]["clicks"] = 25
    for item in queries[1:]:
        item["clicks"] = 1
    result = FreshnessDecayEngine(policy()).assess(record)
    assert result["classification"] == "WINNER_QUERY_PROTECTED"
    assert result["protections"]["preferred_scope"] == "LOCAL_FACT_UPDATE"


def test_fresh_article_is_healthy():
    record = load()
    record["patient"]["article_updated_at"] = datetime.now(timezone.utc).isoformat()
    record["findings"] = []
    record["vital_profiles"][0]["signs"][0]["score"] = 90
    result = FreshnessDecayEngine(policy()).assess(record)
    assert result["classification"] == "RECENT_UPDATE_OBSERVATION"
