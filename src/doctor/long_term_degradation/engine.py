from __future__ import annotations

from typing import Any


class LongTermDegradationEngine:
    RELEVANT_DIAGNOSES = {
        "LONG_TERM_DECAY",
        "SEASONAL_DECLINE",
        "RECOVERY_IN_PROGRESS",
    }

    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.thresholds = policy["thresholds"]

    def assess(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        observation = self._latest_long_term_observation(medical_record)
        if observation is None:
            return self._insufficient("長期観察データが存在しません。")

        facts = observation.get("facts", {})
        windows = list(facts.get("windows", []))
        trend = dict(facts.get("trend", {}))
        if len(windows) < self.thresholds["minimum_windows"]:
            return self._insufficient("長期診断に必要な観察期間が不足しています。")

        visibility_change = float(trend.get("visibility_change_ratio", 0))
        ctr_change = float(trend.get("ctr_change_ratio", 0))
        position_change = trend.get("position_change")
        position_change = float(position_change) if position_change is not None else None
        seasonality_score = trend.get("seasonality_score")
        seasonality_score = (
            float(seasonality_score) if seasonality_score is not None else None
        )
        low_sample = bool(trend.get("low_sample"))
        vital_change, latest_vital_id, previous_vital_id = self._vital_change(
            medical_record
        )
        recurrence = self._recurrence_count(medical_record)

        classification = "STABLE"
        severity = "INFO"
        confidence = 80
        reasons = []

        if self._is_recovery(trend, visibility_change):
            classification = "RECOVERY_IN_PROGRESS"
            severity = "MILD"
            confidence = 88
            reasons.append("直近の長期推移に回復傾向が確認されました。")
        elif (
            seasonality_score is not None
            and seasonality_score >= self.thresholds["seasonality_score"]
            and visibility_change > self.thresholds["sharp_visibility_decline"]
        ):
            classification = "SEASONAL_VARIATION"
            severity = "INFO"
            confidence = 85
            reasons.append("過去期間と類似した季節変動パターンが確認されました。")
        elif visibility_change <= self.thresholds["sharp_visibility_decline"]:
            classification = "SHARP_DEGRADATION"
            severity = "CRITICAL"
            confidence = 94
            reasons.append("表示回数が長期基準から急激に低下しています。")
        elif (
            recurrence >= self.thresholds["recurrence_count"]
            or visibility_change <= self.thresholds["chronic_visibility_decline"]
        ):
            classification = "CHRONIC_DEGRADATION"
            severity = "SEVERE"
            confidence = 90
            reasons.append("長期劣化が継続または再発しています。")
        elif ctr_change <= self.thresholds["ctr_decline"]:
            classification = "CTR_DEGRADATION"
            severity = "MODERATE"
            confidence = 86
            reasons.append("CTRが長期的に低下しています。")
        elif (
            position_change is not None
            and position_change >= self.thresholds["position_decline"]
        ):
            classification = "POSITION_DEGRADATION"
            severity = "MODERATE"
            confidence = 86
            reasons.append("平均順位が長期的に低下しています。")
        else:
            reasons.append("長期推移に重大な劣化は確認されませんでした。")

        if vital_change is not None and vital_change <= self.thresholds["vital_score_decline"]:
            reasons.append(
                f"Vital Scoreが前回より{abs(vital_change)}点低下しています。"
            )
            if classification in {"CHRONIC_DEGRADATION", "SHARP_DEGRADATION"}:
                confidence = min(100, confidence + 4)

        if low_sample:
            confidence = max(0, confidence - 20)
            reasons.append("LOW_SAMPLEのため診断信頼度を下げています。")

        return {
            "classification": classification,
            "confidence": confidence,
            "severity": severity,
            "reasons": reasons,
            "metrics": {
                "window_count": len(windows),
                "visibility_change_ratio": round(visibility_change, 4),
                "ctr_change_ratio": round(ctr_change, 4),
                "position_change": (
                    None if position_change is None else round(position_change, 4)
                ),
                "seasonality_score": seasonality_score,
                "vital_score_change": vital_change,
                "recurrence_count": recurrence,
                "low_sample": low_sample,
            },
            "trace": {
                "long_term_observation_id": observation.get("observation_id"),
                "latest_vital_score_id": latest_vital_id,
                "previous_vital_score_id": previous_vital_id,
                "finding_ids": [
                    item["finding_id"]
                    for item in medical_record.get("findings", [])
                    if item.get("finding_id")
                ],
            },
        }

    def _is_recovery(self, trend, visibility_change):
        return (
            trend.get("classification") == "RECOVERY"
            or visibility_change >= self.thresholds["recovery_visibility_growth"]
            or any(
                value == "RECOVERY_TREND"
                for value in trend.get("signals", [])
            )
        )

    def _recurrence_count(self, medical_record):
        return sum(
            item.get("status") == "CONFIRMED"
            and item.get("diagnosis_code") in self.RELEVANT_DIAGNOSES
            for item in medical_record.get("final_diagnoses", [])
        )

    @staticmethod
    def _latest_long_term_observation(medical_record):
        items = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") == "LONG_TERM"
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
    def _insufficient(reason):
        return {
            "classification": "INSUFFICIENT_HISTORY",
            "confidence": 40,
            "severity": "INFO",
            "reasons": [reason],
            "metrics": {
                "window_count": 0,
                "visibility_change_ratio": 0.0,
                "ctr_change_ratio": 0.0,
                "position_change": None,
                "seasonality_score": None,
                "vital_score_change": None,
                "recurrence_count": 0,
                "low_sample": True,
            },
            "trace": {
                "long_term_observation_id": None,
                "latest_vital_score_id": None,
                "previous_vital_score_id": None,
                "finding_ids": [],
            },
        }
