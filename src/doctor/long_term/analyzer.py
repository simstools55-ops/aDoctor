from __future__ import annotations

from statistics import mean
from typing import Any


class LongTermAnalyzer:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def analyze(self, windows: list[dict[str, Any]]) -> dict[str, Any]:
        if len(windows) < 2:
            return self._empty("STABLE", windows)

        first = windows[0]
        last = windows[-1]

        visibility_change = self._ratio(last["impressions"], first["impressions"])
        click_change = self._ratio(last["clicks"], first["clicks"])
        ctr_change = self._ratio(last["ctr"], first["ctr"])
        position_change = None
        if first.get("position") is not None and last.get("position") is not None:
            position_change = last["position"] - first["position"]

        low_sample = any(
            item["impressions"] < self.policy["minimum_sample"]["impressions_per_window"]
            or item["clicks"] < self.policy["minimum_sample"]["clicks_per_window"]
            for item in windows
        )

        thresholds = self.policy["trend_thresholds"]
        classification = "STABLE"

        recent = windows[-3:] if len(windows) >= 3 else windows
        previous = windows[-6:-3] if len(windows) >= 6 else windows[:-3]
        recent_avg = mean(x["impressions"] for x in recent) if recent else 0
        previous_avg = mean(x["impressions"] for x in previous) if previous else 0

        if previous_avg and (recent_avg - previous_avg) / previous_avg <= -thresholds["sharp_decline_ratio"]:
            classification = "SHARP_DECLINE"
        elif visibility_change <= -thresholds["gradual_decline_ratio"]:
            classification = "GRADUAL_DECLINE"
        elif ctr_change <= -thresholds["ctr_decline_ratio"]:
            classification = "CTR_DECAY"
        elif position_change is not None and position_change >= thresholds["position_decline_absolute"]:
            classification = "POSITION_DECAY"
        elif visibility_change >= thresholds["recovery_ratio"]:
            classification = "RECOVERY"

        seasonality_score = self._seasonality_score(windows)
        if (
            classification == "STABLE"
            and seasonality_score is not None
            and seasonality_score >= thresholds["seasonality_similarity_threshold"]
        ):
            classification = "SEASONAL_PATTERN"

        return {
            "classification": classification,
            "visibility_change_ratio": round(visibility_change, 4),
            "click_change_ratio": round(click_change, 4),
            "ctr_change_ratio": round(ctr_change, 4),
            "position_change": None if position_change is None else round(position_change, 4),
            "seasonality_score": seasonality_score,
            "low_sample": low_sample,
        }

    @staticmethod
    def _ratio(current: float, baseline: float) -> float:
        if baseline == 0:
            return 0.0 if current == 0 else 1.0
        return (current - baseline) / baseline

    @staticmethod
    def _seasonality_score(windows: list[dict[str, Any]]) -> float | None:
        if len(windows) < 10:
            return None
        half = len(windows) // 2
        a = [x["impressions"] for x in windows[:half]]
        b = [x["impressions"] for x in windows[-half:]]
        if not a or not b or len(a) != len(b):
            return None
        max_a = max(a) or 1
        max_b = max(b) or 1
        normalized_a = [x / max_a for x in a]
        normalized_b = [x / max_b for x in b]
        distance = mean(abs(x - y) for x, y in zip(normalized_a, normalized_b))
        return round(max(0.0, 1.0 - distance), 4)

    @staticmethod
    def _empty(classification, windows):
        return {
            "classification": classification,
            "visibility_change_ratio": 0.0,
            "click_change_ratio": 0.0,
            "ctr_change_ratio": 0.0,
            "position_change": None,
            "seasonality_score": None,
            "low_sample": any(x.get("impressions", 0) < 100 for x in windows),
        }
