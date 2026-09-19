from pathlib import Path
import json

from src.doctor.long_term import LongTermAnalyzer


ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "knowledge/observation/long_term/long_term_analysis_policy_v1.json")
    .read_text(encoding="utf-8")
)


def test_detects_gradual_or_sharp_decline():
    windows = []
    for i in range(8):
        windows.append({
            "clicks": 100 - i * 10,
            "impressions": 5000 - i * 500,
            "ctr": 0.02 - i * 0.001,
            "position": 5 + i * 0.2,
        })
    result = LongTermAnalyzer(POLICY).analyze(windows)
    assert result["classification"] in {"GRADUAL_DECLINE", "SHARP_DECLINE"}
    assert result["visibility_change_ratio"] < 0


def test_detects_recovery():
    windows = [
        {"clicks": 10, "impressions": 1000, "ctr": 0.01, "position": 10},
        {"clicks": 20, "impressions": 1400, "ctr": 0.014, "position": 8},
        {"clicks": 30, "impressions": 1800, "ctr": 0.016, "position": 7},
    ]
    result = LongTermAnalyzer(POLICY).analyze(windows)
    assert result["classification"] == "RECOVERY"
