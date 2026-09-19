from pathlib import Path
import json

from src.doctor.treatment_history import TreatmentHistoryAnalyzer


ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "knowledge/observation/treatment_history/treatment_history_policy_v1.json")
    .read_text(encoding="utf-8")
)


def test_detects_worsening():
    baseline = {
        "clicks": 100, "impressions": 3000, "ctr": 0.0333, "position": 6.0
    }
    checkpoints = [{
        "days_after_treatment": 28,
        "clicks": 55, "impressions": 2100, "ctr": 0.0262, "position": 8.5
    }]
    result = TreatmentHistoryAnalyzer(POLICY).analyze(
        baseline=baseline, checkpoints=checkpoints
    )
    assert result["classification"] == "WORSENED"
    assert result["effect_score"] < 0


def test_detects_improvement():
    baseline = {
        "clicks": 50, "impressions": 2000, "ctr": 0.025, "position": 9.0
    }
    checkpoints = [{
        "days_after_treatment": 28,
        "clicks": 80, "impressions": 2600, "ctr": 0.0308, "position": 6.5
    }]
    result = TreatmentHistoryAnalyzer(POLICY).analyze(
        baseline=baseline, checkpoints=checkpoints
    )
    assert result["classification"] == "IMPROVED"
    assert result["effect_score"] > 0


def test_short_follow_up_is_insufficient():
    baseline = {
        "clicks": 50, "impressions": 2000, "ctr": 0.025, "position": 9.0
    }
    checkpoints = [{
        "days_after_treatment": 3,
        "clicks": 60, "impressions": 2200, "ctr": 0.0273, "position": 8.5
    }]
    result = TreatmentHistoryAnalyzer(POLICY).analyze(
        baseline=baseline, checkpoints=checkpoints
    )
    assert result["classification"] == "INSUFFICIENT_FOLLOW_UP"
