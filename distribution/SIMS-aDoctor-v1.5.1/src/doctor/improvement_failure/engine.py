from __future__ import annotations

from typing import Any


class ImprovementFailureEngine:
    FAILURE_DIAGNOSES = {
        "IMPROVEMENT_FAILURE",
        "POST_IMPROVEMENT_WORSENING",
    }

    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.thresholds = policy["thresholds"]

    def assess(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        treatment_observation = self._latest_treatment_history(medical_record)
        if treatment_observation is None:
            return self._insufficient(
                "改善履歴が存在しないため、効果判定を行えません。"
            )

        assessment = treatment_observation["facts"]["assessment"]
        days = int(assessment.get("selected_checkpoint_days", 0))
        low_sample = bool(assessment.get("low_sample"))
        effect_score = float(assessment.get("effect_score", 0))
        metric_changes = dict(assessment.get("metric_changes", {}))
        vital_change, latest_vital_id, previous_vital_id = self._vital_change(
            medical_record
        )
        recurrence = self._failure_recurrence_count(medical_record)

        reasons = []
        classification = "TREATMENT_EFFECTIVE"
        severity = "INFO"
        confidence = 80

        if days < self.policy["minimum_follow_up_days"] or low_sample:
            classification = "INSUFFICIENT_FOLLOW_UP"
            severity = "INFO"
            confidence = 55
            reasons.append(
                "測定期間またはデータ量が不足しているため、改善失敗を確定しません。"
            )
        elif recurrence >= self.thresholds["recurrence_count"]:
            classification = "RECURRENT_FAILURE"
            severity = "SEVERE"
            confidence = 92
            reasons.append(
                f"改善失敗または改善後悪化が{recurrence}回確認されています。"
            )
        elif self._is_wrong_direction(effect_score, metric_changes, vital_change):
            classification = "POSSIBLE_WRONG_TREATMENT_DIRECTION"
            severity = "SEVERE"
            confidence = 86
            reasons.append(
                "前回改善後に複数の主要指標またはVital Scoreが同時に悪化しています。"
            )
        elif effect_score <= self.thresholds["worsening_effect_score"]:
            classification = "POST_TREATMENT_WORSENING"
            severity = "SEVERE"
            confidence = 90
            reasons.append(
                "改善前と比べて総合効果スコアが悪化基準を下回りました。"
            )
        elif abs(effect_score) < self.thresholds["no_effect_absolute_effect_score"]:
            classification = "NO_MEASURABLE_EFFECT"
            severity = "MODERATE"
            confidence = 82
            reasons.append(
                "改善前後で有意な効果を確認できませんでした。"
            )
        else:
            reasons.append("改善後に一定の改善効果が確認されています。")

        self._append_metric_reasons(
            reasons, metric_changes, vital_change
        )

        return {
            "classification": classification,
            "confidence": confidence,
            "severity": severity,
            "reasons": reasons,
            "metrics": {
                "effect_score": round(effect_score, 4),
                "selected_checkpoint_days": days,
                "vital_score_change": vital_change,
                "metric_changes": metric_changes,
                "failure_recurrence_count": recurrence,
                "low_sample": low_sample,
            },
            "trace": {
                "treatment_history_observation_id":
                    treatment_observation.get("observation_id"),
                "latest_vital_score_id": latest_vital_id,
                "previous_vital_score_id": previous_vital_id,
                "finding_ids": [
                    item["finding_id"]
                    for item in medical_record.get("findings", [])
                    if item.get("finding_id")
                ],
            },
        }

    def _is_wrong_direction(self, effect_score, changes, vital_change):
        t = self.thresholds
        negative_metrics = sum(
            value <= threshold
            for value, threshold in [
                (changes.get("ctr", 0), t["ctr_decline_ratio"]),
                (changes.get("position", 0), t["position_decline_ratio"]),
                (changes.get("impressions", 0), t["impression_decline_ratio"]),
            ]
        )
        vital_bad = (
            vital_change is not None
            and vital_change <= t["vital_score_decline"]
        )
        return (
            effect_score <= t["wrong_direction_effect_score"]
            and (negative_metrics >= 2 or (negative_metrics >= 1 and vital_bad))
        )

    def _failure_recurrence_count(self, medical_record):
        diagnoses = medical_record.get("final_diagnoses", [])
        return sum(
            item.get("status") == "CONFIRMED"
            and item.get("diagnosis_code") in self.FAILURE_DIAGNOSES
            for item in diagnoses
        )

    @staticmethod
    def _latest_treatment_history(medical_record):
        items = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") == "TREATMENT_HISTORY"
        ]
        return items[-1] if items else None

    @staticmethod
    def _vital_change(medical_record):
        scores = [
            item for item in medical_record.get("vital_scores", [])
            if item.get("overall_score") is not None
        ]
        if len(scores) < 2:
            latest = scores[-1]["score_id"] if scores else None
            return None, latest, None
        previous, latest = scores[-2], scores[-1]
        return (
            int(latest["overall_score"]) - int(previous["overall_score"]),
            latest["score_id"],
            previous["score_id"],
        )

    @staticmethod
    def _append_metric_reasons(reasons, changes, vital_change):
        labels = {
            "clicks": "クリック数",
            "impressions": "表示回数",
            "ctr": "CTR",
            "position": "順位健康度",
        }
        for key, label in labels.items():
            value = changes.get(key)
            if value is not None and value <= -0.15:
                reasons.append(f"{label}が改善前より悪化しています。")
        if vital_change is not None and vital_change <= -8:
            reasons.append(
                f"Vital Scoreが改善前より{abs(vital_change)}点低下しています。"
            )

    @staticmethod
    def _insufficient(reason):
        return {
            "classification": "INSUFFICIENT_FOLLOW_UP",
            "confidence": 40,
            "severity": "INFO",
            "reasons": [reason],
            "metrics": {
                "effect_score": 0.0,
                "selected_checkpoint_days": 0,
                "vital_score_change": None,
                "metric_changes": {},
                "failure_recurrence_count": 0,
                "low_sample": True,
            },
            "trace": {
                "treatment_history_observation_id": None,
                "latest_vital_score_id": None,
                "previous_vital_score_id": None,
                "finding_ids": [],
            },
        }
