from __future__ import annotations

from typing import Any

from .models import BatchItem


SEVERITY_SCORE = {
    "CRITICAL": 100,
    "SEVERE": 80,
    "MODERATE": 60,
    "MILD": 35,
    "INFO": 10,
    None: 0,
}


class BatchPriorityCalculator:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def calculate(self, item: BatchItem) -> float:
        weights = self.policy["priority"]["weights"]
        levels = self.policy["priority"]["levels"]

        profile = item.longitudinal_profile or {}
        longitudinal_level = profile.get("follow_up_priority", "UNKNOWN")
        longitudinal = levels.get(longitudinal_level, levels["UNKNOWN"])

        severity = SEVERITY_SCORE.get(
            profile.get("latest_severity")
            or (item.current_metrics or {}).get("severity"),
            0,
        )
        recurrence = min(
            100,
            float(
                profile.get("recurrence", {}).get("maximum_recurrence_count", 0)
            ) * 25,
        )
        metrics = item.current_metrics or {}
        impressions = float(metrics.get("impressions", 0))
        clicks = float(metrics.get("clicks", 0))
        traffic_opportunity = min(
            100,
            impressions / 100 + max(0, impressions - clicks * 20) / 200,
        )

        score = (
            longitudinal * weights["longitudinal_priority"]
            + severity * weights["severity"]
            + recurrence * weights["recurrence"]
            + traffic_opportunity * weights["traffic_opportunity"]
        )
        return round(max(0, min(100, score)), 2)
