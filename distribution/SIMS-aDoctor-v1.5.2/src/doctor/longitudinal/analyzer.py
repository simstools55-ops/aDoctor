from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any


class LongitudinalAnalyzer:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.thresholds = policy["thresholds"]

    def analyze(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        diagnoses = list(medical_record.get("final_diagnoses", []))
        history_observations = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") == "TREATMENT_HISTORY"
        ]

        confirmed = [item for item in diagnoses if item.get("status") == "CONFIRMED"]
        deferred = [item for item in diagnoses if item.get("status") == "DEFERRED"]

        diagnosis_codes = [
            item.get("diagnosis_code") for item in confirmed
            if item.get("diagnosis_code")
        ]
        diagnosis_counts = Counter(diagnosis_codes)
        defer_counts = Counter(
            item.get("defer_reason") for item in deferred if item.get("defer_reason")
        )

        treatment_classifications = [
            item.get("facts", {}).get("assessment", {}).get("classification")
            for item in history_observations
        ]
        treatment_classifications = [item for item in treatment_classifications if item]

        success_count = sum(
            item in {"IMPROVED", "PARTIAL_IMPROVEMENT"}
            for item in treatment_classifications
        )
        failure_count = sum(item == "NO_EFFECT" for item in treatment_classifications)
        worsening_count = sum(item == "WORSENED" for item in treatment_classifications)
        mixed_count = sum(item == "MIXED_RESPONSE" for item in treatment_classifications)
        measurable = success_count + failure_count + worsening_count + mixed_count
        success_ratio = success_count / measurable if measurable else 0.0
        failure_ratio = (
            (failure_count + worsening_count) / measurable if measurable else 0.0
        )

        recurrence_count = self.thresholds["recurrence_count"]
        recurrent = sorted(
            code for code, count in diagnosis_counts.items()
            if count >= recurrence_count
        )
        dominant = None
        maximum = 0
        if diagnosis_counts:
            dominant, maximum = diagnosis_counts.most_common(1)[0]

        recent_recurrence = self._recent_recurrence(confirmed)
        patterns = self._patterns(
            diagnosis_counts=diagnosis_counts,
            defer_counts=defer_counts,
            success_ratio=success_ratio,
            failure_ratio=failure_ratio,
            worsening_count=worsening_count,
            mixed_count=mixed_count,
            recent_recurrence=recent_recurrence,
        )
        status = self._status(
            confirmed_count=len(confirmed),
            recurrent=recurrent,
            maximum_recurrence=maximum,
            success_ratio=success_ratio,
            failure_ratio=failure_ratio,
            latest_code=diagnosis_codes[-1] if diagnosis_codes else None,
        )
        priority = self._priority(
            status=status,
            maximum_recurrence=maximum,
            worsening_count=worsening_count,
            recent_recurrence=recent_recurrence,
        )

        return {
            "profile_status": status,
            "follow_up_priority": priority,
            "summary": self._summary(status, dominant, maximum),
            "diagnosis_history": {
                "total_diagnoses": len(diagnoses),
                "confirmed_count": len(confirmed),
                "deferred_count": len(deferred),
                "diagnosis_counts": dict(diagnosis_counts),
                "defer_reason_counts": dict(defer_counts),
                "latest_diagnosis": diagnosis_codes[-1] if diagnosis_codes else None,
            },
            "treatment_response": {
                "success_count": success_count,
                "failure_count": failure_count,
                "worsening_count": worsening_count,
                "mixed_count": mixed_count,
                "success_ratio": round(success_ratio, 4),
                "failure_ratio": round(failure_ratio, 4),
            },
            "recurrence": {
                "recurrent_diagnoses": recurrent,
                "dominant_diagnosis": dominant,
                "maximum_recurrence_count": maximum,
                "recent_recurrence": recent_recurrence,
            },
            "patterns": patterns,
            "trace": {
                "diagnosis_ids": [
                    item["diagnosis_id"] for item in diagnoses
                    if item.get("diagnosis_id")
                ],
                "treatment_history_observation_ids": [
                    item["observation_id"] for item in history_observations
                    if item.get("observation_id")
                ],
            },
        }

    def _recent_recurrence(self, confirmed: list[dict[str, Any]]) -> bool:
        if len(confirmed) < 2:
            return False
        recent = confirmed[-self.thresholds["recent_window_cases"]:]
        codes = [
            item.get("diagnosis_code") for item in recent
            if item.get("diagnosis_code")
        ]
        return any(count >= 2 for count in Counter(codes).values())

    def _patterns(
        self,
        *,
        diagnosis_counts,
        defer_counts,
        success_ratio,
        failure_ratio,
        worsening_count,
        mixed_count,
        recent_recurrence,
    ):
        patterns = []
        if any(count >= self.thresholds["recurrence_count"] for count in diagnosis_counts.values()):
            patterns.append("REPEATED_DIAGNOSIS")
        if any(count >= self.thresholds["chronic_case_count"] for count in diagnosis_counts.values()):
            patterns.append("CHRONIC_RECURRENCE")
        if success_ratio >= self.thresholds["treatment_success_ratio_good"]:
            patterns.append("GOOD_TREATMENT_RESPONSE")
        if failure_ratio >= self.thresholds["treatment_failure_ratio_high"]:
            patterns.append("POOR_TREATMENT_RESPONSE")
        if worsening_count:
            patterns.append("POST_TREATMENT_WORSENING_HISTORY")
        if mixed_count:
            patterns.append("UNSTABLE_TREATMENT_RESPONSE")
        if defer_counts:
            patterns.append("REPEATED_DIAGNOSTIC_UNCERTAINTY")
        if recent_recurrence:
            patterns.append("RECENT_RECURRENCE")
        return patterns

    def _status(
        self,
        *,
        confirmed_count,
        recurrent,
        maximum_recurrence,
        success_ratio,
        failure_ratio,
        latest_code,
    ):
        if confirmed_count < self.policy["minimum_completed_diagnoses"]:
            return "INSUFFICIENT_HISTORY"
        if maximum_recurrence >= self.thresholds["chronic_case_count"]:
            return "CHRONIC"
        if recurrent:
            return "RECURRENT"
        if failure_ratio >= self.thresholds["treatment_failure_ratio_high"]:
            return "TREATMENT_RESISTANT"
        if success_ratio >= self.thresholds["treatment_success_ratio_good"]:
            return "TREATMENT_RESPONSIVE"
        if latest_code in {"RECOVERY_IN_PROGRESS", "TREATMENT_SUCCESS"}:
            return "RECOVERING"
        return "STABLE"

    @staticmethod
    def _priority(*, status, maximum_recurrence, worsening_count, recent_recurrence):
        if worsening_count and recent_recurrence:
            return "URGENT"
        if status in {"CHRONIC", "TREATMENT_RESISTANT"}:
            return "HIGH"
        if status in {"RECURRENT", "RECOVERING"} or maximum_recurrence >= 2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _summary(status, dominant, count):
        labels = {
            "INSUFFICIENT_HISTORY": "長期傾向を判断するには診療履歴が不足しています。",
            "STABLE": "現在の診療履歴では明確な再発傾向は確認されていません。",
            "RECURRENT": "同じ問題が繰り返し診断されています。",
            "CHRONIC": "同じ問題が複数回再発し、慢性化している可能性があります。",
            "TREATMENT_RESPONSIVE": "これまでの改善に対して良好な反応が確認されています。",
            "TREATMENT_RESISTANT": "複数回の改善でも十分な効果が得られていません。",
            "RECOVERING": "直近の診療では回復傾向が確認されています。",
        }
        summary = labels[status]
        if dominant:
            summary += f" 最多診断は{dominant}で、{count}回です。"
        return summary
