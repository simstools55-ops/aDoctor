from __future__ import annotations

from typing import Any


class TreatmentHistoryAnalyzer:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def analyze(
        self,
        *,
        baseline: dict[str, Any],
        checkpoints: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not checkpoints:
            raise ValueError("At least one checkpoint is required")

        checkpoint = checkpoints[-1]
        minimum_days = self.policy["minimum_follow_up_days"]
        low_sample = (
            baseline["impressions"] < self.policy["thresholds"]["minimum_baseline_impressions"]
            or checkpoint["impressions"] < self.policy["thresholds"]["minimum_baseline_impressions"]
        )

        changes = {
            "clicks": self._relative_change(checkpoint["clicks"], baseline["clicks"]),
            "impressions": self._relative_change(checkpoint["impressions"], baseline["impressions"]),
            "ctr": self._relative_change(checkpoint["ctr"], baseline["ctr"]),
            "position": self._position_health_change(
                checkpoint.get("position"), baseline.get("position")
            ),
        }
        effect_score = sum(
            changes[name] * weight
            for name, weight in self.policy["metric_weights"].items()
        )

        if checkpoint["days_after_treatment"] < minimum_days:
            classification = "INSUFFICIENT_FOLLOW_UP"
        elif low_sample and effect_score < 0:
            classification = "INSUFFICIENT_FOLLOW_UP"
        else:
            classification = self._classify(effect_score, changes)

        return {
            "classification": classification,
            "effect_score": round(effect_score, 4),
            "metric_changes": {
                key: round(value, 4) for key, value in changes.items()
            },
            "selected_checkpoint_days": checkpoint["days_after_treatment"],
            "low_sample": low_sample,
        }

    def _classify(self, score: float, changes: dict[str, float]) -> str:
        t = self.policy["thresholds"]
        positives = sum(value >= t["partial_improvement_score"] for value in changes.values())
        negatives = sum(value <= -t["partial_improvement_score"] for value in changes.values())
        severe_negative = any(
            value <= t["single_metric_guardrail_decline"] for value in changes.values()
        )

        if positives and negatives:
            if score <= t["worsened_score"] or severe_negative:
                return "WORSENED"
            return "MIXED_RESPONSE"
        if score >= t["improved_score"]:
            return "IMPROVED"
        if score >= t["partial_improvement_score"]:
            return "PARTIAL_IMPROVEMENT"
        if score <= t["worsened_score"] or severe_negative:
            return "WORSENED"
        if abs(score) < t["no_effect_absolute_score"]:
            return "NO_EFFECT"
        return "MIXED_RESPONSE"

    @staticmethod
    def _relative_change(current: float, baseline: float) -> float:
        if baseline == 0:
            return 0.0 if current == 0 else 1.0
        return (current - baseline) / baseline

    @staticmethod
    def _position_health_change(current: float | None, baseline: float | None) -> float:
        if current is None or baseline is None:
            return 0.0
        if baseline == 0:
            return 0.0
        # A lower search position is healthier, so invert the direction.
        return (baseline - current) / baseline
