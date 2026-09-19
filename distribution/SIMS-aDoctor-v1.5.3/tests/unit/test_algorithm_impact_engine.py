from pathlib import Path
import json

from src.doctor.algorithm_impact import AlgorithmImpactEngine

ROOT = Path(__file__).resolve().parents[2]


def _engine():
    policy = json.loads((ROOT / "knowledge/algorithm_impact/algorithm_impact_policy_v1.json").read_text(encoding="utf-8"))
    return AlgorithmImpactEngine(policy)


def test_temporal_overlap_alone_does_not_claim_high_impact():
    record = {"algorithm_context": {
        "update": {"detected": True, "source_status": "OFFICIAL_CONFIRMED", "rollout_status": "COMPLETED"},
        "correlation": {"temporal": "HIGH", "site_wide": "NONE", "segment": "UNKNOWN", "article": "HIGH", "serp": "NONE"}
    }}
    result = _engine().assess(record)
    assert result["status"] in {"LOW", "POSSIBLE"}
    assert result["role"] != "PRIMARY_FACTOR"
    assert "ARTICLE_ONLY_SHIFT_DURING_UPDATE" in result["reason_codes"]


def test_site_and_serp_corroboration_can_reach_high():
    record = {"algorithm_context": {
        "update": {"detected": True, "source_status": "OFFICIAL_CONFIRMED", "rollout_status": "IN_PROGRESS"},
        "correlation": {"temporal": "HIGH", "site_wide": "HIGH", "segment": "HIGH", "article": "HIGH", "serp": "HIGH"}
    }}
    result = _engine().assess(record)
    assert result["status"] == "HIGH"
    assert result["confidence"] == "HIGH"
    assert result["role"] == "PRIMARY_FACTOR"
    assert "UPDATE_ROLLOUT_IN_PROGRESS" in result["reason_codes"]
