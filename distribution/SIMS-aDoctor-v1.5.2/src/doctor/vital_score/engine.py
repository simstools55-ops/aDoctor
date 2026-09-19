from __future__ import annotations

from typing import Any


class VitalScoreEngine:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.weights = policy["weights"]

    def calculate(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        profile = (
            medical_record.get("vital_profiles", [])[-1]
            if medical_record.get("vital_profiles") else None
        )
        signs = profile.get("signs", []) if profile else []
        signs_by_code = {
            item["code"]: item
            for item in signs
            if item.get("score") is not None
        }

        available = [
            code for code in self.weights
            if code in signs_by_code
        ]
        missing = [
            code for code in self.weights
            if code not in signs_by_code
        ]
        minimum = self.policy["missing_value"]["minimum_available_signs"]

        if len(available) < minimum:
            return {
                "score_status": "INSUFFICIENT_DATA",
                "overall_score": None,
                "health_band": None,
                "available_sign_count": len(available),
                "missing_signs": missing,
                "components": [],
                "adjustments": {
                    "penalty": 0,
                    "bonus": 0,
                    "reasons": ["利用可能なVital Signが不足しています。"],
                },
                "negative_factors": [],
                "positive_factors": [],
                "trace": self._trace(medical_record, profile),
            }

        total_weight = sum(self.weights[code] for code in available)
        components = []
        for code in available:
            raw_score = int(round(signs_by_code[code]["score"]))
            effective_weight = self.weights[code] / total_weight
            weighted_score = raw_score * effective_weight
            components.append({
                "code": code,
                "raw_score": raw_score,
                "weight": self.weights[code],
                "effective_weight": round(effective_weight, 6),
                "weighted_score": round(weighted_score, 4),
            })

        base_score = sum(item["weighted_score"] for item in components)
        adjustment = self._adjustments(medical_record, signs)
        overall = round(
            max(
                0,
                min(
                    100,
                    base_score - adjustment["penalty"] + adjustment["bonus"],
                ),
            )
        )

        return {
            "score_status": "CALCULATED",
            "overall_score": overall,
            "health_band": self._health_band(overall),
            "available_sign_count": len(available),
            "missing_signs": missing,
            "components": components,
            "adjustments": adjustment,
            "negative_factors": self._negative_factors(
                components, medical_record
            ),
            "positive_factors": self._positive_factors(
                components, medical_record
            ),
            "trace": self._trace(medical_record, profile),
        }

    def _adjustments(self, medical_record, signs):
        config = self.policy["adjustments"]
        penalty = 0
        bonus = 0
        reasons = []

        if any(bool(item.get("low_sample")) for item in signs):
            penalty += config["low_sample_penalty"]
            reasons.append("LOW_SAMPLEのため信頼性補正を適用しました。")

        critical = sum(
            item.get("severity") == "CRITICAL"
            for item in medical_record.get("findings", [])
        )
        severe = sum(
            item.get("severity") == "SEVERE"
            for item in medical_record.get("findings", [])
        )
        if critical:
            value = critical * config["critical_finding_penalty"]
            penalty += value
            reasons.append(f"CRITICAL所見{critical}件による減点です。")
        if severe:
            value = severe * config["severe_finding_penalty"]
            penalty += value
            reasons.append(f"SEVERE所見{severe}件による減点です。")

        if any(
            item.get("finding_code") in {
                "RECOVERY_TREND",
                "IMPROVEMENT_CONFIRMED",
            }
            for item in medical_record.get("findings", [])
        ):
            bonus += config["recovery_bonus"]
            reasons.append("回復または改善確認による加点です。")

        penalty = min(penalty, config["maximum_total_penalty"])
        bonus = min(bonus, config["maximum_total_bonus"])
        return {
            "penalty": penalty,
            "bonus": bonus,
            "reasons": reasons,
        }

    def _negative_factors(self, components, medical_record):
        limit = self.policy["explanation"]["top_negative_factors"]
        component_factors = [
            {
                "type": "VITAL_SIGN",
                "code": item["code"],
                "impact": round((100 - item["raw_score"]) * item["effective_weight"], 4),
                "message": f"{item['code']}が総合スコアを下げています。",
            }
            for item in components
            if item["raw_score"] < 60
        ]
        finding_factors = [
            {
                "type": "FINDING",
                "code": item["finding_code"],
                "impact": 12 if item.get("severity") == "CRITICAL" else 6,
                "message": f"{item['finding_code']}が確認されています。",
            }
            for item in medical_record.get("findings", [])
            if item.get("severity") in {"CRITICAL", "SEVERE"}
        ]
        factors = component_factors + finding_factors
        factors.sort(key=lambda item: (-item["impact"], item["code"]))
        return factors[:limit]

    def _positive_factors(self, components, medical_record):
        limit = self.policy["explanation"]["top_positive_factors"]
        factors = [
            {
                "type": "VITAL_SIGN",
                "code": item["code"],
                "impact": round(item["raw_score"] * item["effective_weight"], 4),
                "message": f"{item['code']}は良好です。",
            }
            for item in components
            if item["raw_score"] >= 75
        ]
        if any(
            item.get("finding_code") == "RECOVERY_TREND"
            for item in medical_record.get("findings", [])
        ):
            factors.append({
                "type": "FINDING",
                "code": "RECOVERY_TREND",
                "impact": 5,
                "message": "回復傾向が確認されています。",
            })
        factors.sort(key=lambda item: (-item["impact"], item["code"]))
        return factors[:limit]

    def _health_band(self, score):
        for band in self.policy["health_bands"]:
            if score >= band["minimum"]:
                return band["code"]
        return "CRITICAL"

    @staticmethod
    def _trace(medical_record, profile):
        return {
            "vital_profile_id": profile.get("profile_id") if profile else None,
            "finding_ids": [
                item["finding_id"]
                for item in medical_record.get("findings", [])
                if item.get("finding_id")
            ],
            "observation_ids": [
                item["observation_id"]
                for item in medical_record.get("observations", [])
                if item.get("observation_id")
            ],
        }
