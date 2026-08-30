from __future__ import annotations

from typing import Any


class CompositeDiagnosisEngine:
    ASSESSMENT_FIELDS = [
        "improvement_failure_assessments",
        "long_term_degradation_assessments",
        "ctr_opportunity_assessments",
        "position_opportunity_assessments",
        "intent_drift_assessments",
        "freshness_decay_assessments",
        "cannibalization_assessments",
    ]

    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.t = policy["thresholds"]

    def diagnose(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        latest = self._latest_assessments(medical_record)
        vital_score = self._latest_vital_score(medical_record)
        content_integrity = self._vital_sign_score(medical_record, "CONTENT_INTEGRITY")
        competition = self._vital_sign_score(medical_record, "COMPETITION_RESILIENCE")
        algorithm = (medical_record.get("algorithm_impact_assessments") or [None])[-1]

        completed_count = sum(value is not None for value in latest.values())
        low_sample = any(
            bool((assessment or {}).get("metrics", {}).get("low_sample"))
            or (assessment or {}).get("classification") in {
                "INSUFFICIENT_DATA",
                "INSUFFICIENT_HISTORY",
                "INSUFFICIENT_FOLLOW_UP",
                "FOLLOW_UP_REQUIRED",
            }
            for assessment in latest.values()
        )
        recent_change = any(
            (assessment or {}).get("classification") in {
                "RECENT_CHANGE_OBSERVATION",
                "RECENT_UPDATE_OBSERVATION",
            }
            for assessment in latest.values()
        )
        winner_protected = any(
            bool((assessment or {}).get("protections", {}).get("winner_query_protected"))
            or (assessment or {}).get("classification") == "WINNER_QUERY_PROTECTED"
            for assessment in latest.values()
        )
        cannibal = latest.get("cannibalization_assessments") or {}
        merge_required = cannibal.get("classification") == "MERGE_CANDIDATE"
        role_separation = (
            cannibal.get("classification") == "ROLE_SEPARATION_RECOMMENDED"
        )

        risk_score, score_reasons = self._risk_score(
            latest=latest,
            content_integrity=content_integrity,
            competition=competition,
        )
        health_score = vital_score if vital_score is not None else max(0, 100 - risk_score)
        weighted_score = round((risk_score + (100 - health_score)) / 2)
        confidence = self._confidence(latest, completed_count)
        reasons = list(score_reasons)

        if completed_count < self.t["minimum_completed_assessments"]:
            final = "FOLLOW_UP_REQUIRED"
            severity = "INFO"
            reasons.insert(0, "総合診断に必要な専門診断数が不足しています。")
        elif low_sample:
            final = "FOLLOW_UP_REQUIRED"
            severity = "INFO"
            reasons.insert(0, "LOW_SAMPLEまたは測定不足を安全優先しました。")
        elif recent_change:
            final = "OBSERVE_ONLY"
            severity = "INFO"
            reasons.insert(0, "直近の変更・更新後であるため経過観察を優先します。")
        elif winner_protected:
            final = self._winner_safe_diagnosis(latest, risk_score)
            severity = "MODERATE" if final == "LOCAL_OPTIMIZATION" else "INFO"
            reasons.insert(0, "Winner Query保護により大規模変更を制限します。")
        elif merge_required:
            final = "MERGE_RECOMMENDED"
            severity = "SEVERE"
            reasons.insert(0, "カニバリ診断でMerge候補が確認されました。")
        elif role_separation:
            final = "LOCAL_OPTIMIZATION"
            severity = "MODERATE"
            reasons.insert(0, "記事統合ではなく役割分担の明確化を優先します。")
        elif self._new_article_candidate(latest):
            final = "NEW_ARTICLE_RECOMMENDED"
            severity = "SEVERE"
            reasons.insert(0, "既存記事の役割変更より新しい検索意図の分離が適切です。")
        elif self._full_rewrite_candidate(latest, content_integrity, risk_score):
            final = "FULL_REWRITE_RECOMMENDED"
            severity = "SEVERE"
            reasons.insert(0, "複数領域の重大な問題が重なっています。")
        elif self._local_optimization_candidate(latest, risk_score):
            final = "LOCAL_OPTIMIZATION"
            severity = "MODERATE"
            reasons.insert(0, "局所的な改善で回復できる可能性があります。")
        elif self._minor_refresh_candidate(latest):
            final = "MINOR_REFRESH"
            severity = "MILD"
            reasons.insert(0, "限定的な情報更新が適切です。")
        else:
            final = "HEALTHY"
            severity = "INFO"
            reasons.insert(0, "重大な治療対象は確認されませんでした。")

        content_integrity_severe = (
            content_integrity is not None
            and content_integrity < self.t["severe_content_integrity_max"]
        )
        algorithm_wait_recommended = bool(
            algorithm
            and algorithm.get("status") in {"LIKELY", "HIGH"}
            and str((algorithm.get("update") or {}).get("rollout_status") or "").upper() == "IN_PROGRESS"
            and not content_integrity_severe
        )
        if algorithm_wait_recommended:
            reasons.insert(0, "Googleアップデート展開中の可能性が高いため、治療タイミングは経過観察を優先できます。")

        full_rewrite_allowed = not winner_protected and not recent_change and not low_sample
        new_article_allowed = (
            final == "NEW_ARTICLE_RECOMMENDED"
            and not merge_required
            and not winner_protected
        )

        priority = self._priority(
            final=final,
            risk_score=risk_score,
            confidence=confidence,
        )

        return {
            "final_diagnosis": final,
            "confidence": confidence,
            "severity": severity,
            "priority": priority,
            "reasons": self._dedupe(reasons),
            "score": {
                "base_score": risk_score,
                "weighted_score": weighted_score,
                "risk_score": risk_score,
                "health_score": health_score,
            },
            "safety": {
                "winner_query_protected": winner_protected,
                "recent_change_or_update": recent_change,
                "low_sample_or_insufficient": low_sample,
                "merge_required": merge_required,
                "new_article_allowed": new_article_allowed,
                "full_rewrite_allowed": full_rewrite_allowed,
                "content_integrity_severe": content_integrity_severe,
                "algorithm_wait_recommended": algorithm_wait_recommended,
            },
            "algorithm_assessment": algorithm,
            "supporting_assessments": [
                {
                    "assessment_type": field,
                    "assessment_id": assessment.get("assessment_id"),
                    "classification": assessment.get("classification"),
                    "confidence": assessment.get("confidence"),
                    "severity": assessment.get("severity"),
                }
                for field, assessment in latest.items()
                if assessment is not None
            ],
            "trace": {
                "vital_score_id": self._latest_vital_score_id(medical_record),
                "vital_profile_id": (
                    medical_record.get("vital_profiles", [{}])[-1].get("profile_id")
                    if medical_record.get("vital_profiles") else None
                ),
                "assessment_ids": [
                    assessment.get("assessment_id")
                    for assessment in latest.values()
                    if assessment and assessment.get("assessment_id")
                ],
            },
        }

    def _risk_score(self, *, latest, content_integrity, competition):
        weights = self.policy["weights"]
        score = 0.0
        reasons = []

        mapping = {
            "ctr_opportunity_assessments": ("ctr_opportunity", {
                "CTR_OPPORTUNITY": 55,
                "HIGH_CTR_OPPORTUNITY": 80,
                "WINNER_QUERY_PROTECTED": 35,
            }),
            "position_opportunity_assessments": ("position_opportunity", {
                "POSITION_OPPORTUNITY": 55,
                "HIGH_POSITION_OPPORTUNITY": 80,
                "QUERY_FOCUSED_OPPORTUNITY": 65,
                "LOW_VISIBILITY_OR_MISALIGNMENT": 85,
            }),
            "intent_drift_assessments": ("intent_drift", {
                "INTENT_DRIFT": 85,
                "TOPIC_DISPERSION": 90,
                "EMERGING_INTENT_TRANSITION": 70,
            }),
            "freshness_decay_assessments": ("freshness_decay", {
                "PARTIAL_FRESHNESS_DECAY": 55,
                "SEVERE_FRESHNESS_DECAY": 90,
                "WINNER_QUERY_PROTECTED": 40,
            }),
            "cannibalization_assessments": ("cannibalization", {
                "POSSIBLE_CANNIBALIZATION": 55,
                "CONFIRMED_CANNIBALIZATION": 80,
                "MERGE_CANDIDATE": 100,
                "ROLE_SEPARATION_RECOMMENDED": 60,
            }),
        }

        for field, (weight_key, values) in mapping.items():
            assessment = latest.get(field) or {}
            classification = assessment.get("classification")
            value = values.get(classification, 0)
            score += value * weights[weight_key]
            if value:
                reasons.append(
                    f"{field}の{classification}を総合リスクへ反映しました。"
                )

        if content_integrity is not None:
            value = 100 - content_integrity
            score += value * weights["content_integrity"]
            if content_integrity < self.t["severe_content_integrity_max"]:
                reasons.append("Content Integrityが低下しています。")

        if competition is not None:
            value = 100 - competition
            score += value * weights["competition"]
            if competition < 45:
                reasons.append("Competition Resilienceが低下しています。")

        improvement = latest.get("improvement_failure_assessments") or {}
        if improvement.get("classification") in {
            "POST_TREATMENT_WORSENING",
            "POSSIBLE_WRONG_TREATMENT_DIRECTION",
            "RECURRENT_FAILURE",
        }:
            score += 15
            reasons.append("改善失敗または改善後悪化を追加リスクとして反映しました。")

        long_term = latest.get("long_term_degradation_assessments") or {}
        if long_term.get("classification") in {
            "CHRONIC_DEGRADATION",
            "SHARP_DEGRADATION",
        }:
            score += 15
            reasons.append("長期劣化を追加リスクとして反映しました。")

        return min(100, round(score)), reasons

    def _confidence(self, latest, completed_count):
        confidences = [
            int(assessment.get("confidence", 0))
            for assessment in latest.values()
            if assessment is not None
        ]
        if not confidences:
            return 0
        base = sum(confidences) / len(confidences)
        completeness_bonus = min(10, completed_count)
        return max(0, min(100, round(base + completeness_bonus)))

    @staticmethod
    def _winner_safe_diagnosis(latest, risk_score):
        freshness = latest.get("freshness_decay_assessments") or {}
        ctr = latest.get("ctr_opportunity_assessments") or {}
        position = latest.get("position_opportunity_assessments") or {}
        if (
            freshness.get("classification") in {
                "PARTIAL_FRESHNESS_DECAY",
                "WINNER_QUERY_PROTECTED",
            }
            or ctr.get("classification") in {
                "CTR_OPPORTUNITY",
                "HIGH_CTR_OPPORTUNITY",
                "WINNER_QUERY_PROTECTED",
            }
            or position.get("classification") in {
                "POSITION_OPPORTUNITY",
                "QUERY_FOCUSED_OPPORTUNITY",
                "WINNER_QUERY_PROTECTED",
            }
        ):
            return "LOCAL_OPTIMIZATION"
        return "OBSERVE_ONLY"

    @staticmethod
    def _new_article_candidate(latest):
        intent = latest.get("intent_drift_assessments") or {}
        position = latest.get("position_opportunity_assessments") or {}
        cannibal = latest.get("cannibalization_assessments") or {}
        return (
            intent.get("classification") == "EMERGING_INTENT_TRANSITION"
            and int(intent.get("confidence", 0)) >= 85
            and position.get("classification") == "LOW_VISIBILITY_OR_MISALIGNMENT"
            and cannibal.get("classification") not in {
                "MERGE_CANDIDATE",
                "CONFIRMED_CANNIBALIZATION",
            }
        )

    def _full_rewrite_candidate(self, latest, content_integrity, risk_score):
        intent = latest.get("intent_drift_assessments") or {}
        freshness = latest.get("freshness_decay_assessments") or {}
        long_term = latest.get("long_term_degradation_assessments") or {}
        improvement = latest.get("improvement_failure_assessments") or {}
        serious = sum([
            intent.get("classification") in {"INTENT_DRIFT", "TOPIC_DISPERSION"},
            freshness.get("classification") == "SEVERE_FRESHNESS_DECAY",
            long_term.get("classification") in {
                "CHRONIC_DEGRADATION", "SHARP_DEGRADATION"
            },
            improvement.get("classification") in {
                "POSSIBLE_WRONG_TREATMENT_DIRECTION", "RECURRENT_FAILURE"
            },
            content_integrity is not None
            and content_integrity < self.t["severe_content_integrity_max"],
        ])
        return serious >= 2 or risk_score >= self.t["full_rewrite_score"]

    def _local_optimization_candidate(self, latest, risk_score):
        ctr = latest.get("ctr_opportunity_assessments") or {}
        position = latest.get("position_opportunity_assessments") or {}
        freshness = latest.get("freshness_decay_assessments") or {}
        return (
            risk_score >= self.t["local_optimization_score"]
            or ctr.get("classification") in {
                "CTR_OPPORTUNITY", "HIGH_CTR_OPPORTUNITY"
            }
            or position.get("classification") in {
                "POSITION_OPPORTUNITY",
                "HIGH_POSITION_OPPORTUNITY",
                "QUERY_FOCUSED_OPPORTUNITY",
            }
            or freshness.get("classification") == "PARTIAL_FRESHNESS_DECAY"
        )

    @staticmethod
    def _minor_refresh_candidate(latest):
        freshness = latest.get("freshness_decay_assessments") or {}
        return freshness.get("classification") == "PARTIAL_FRESHNESS_DECAY"

    @staticmethod
    def _priority(*, final, risk_score, confidence):
        base = {
            "MERGE_RECOMMENDED": 95,
            "FULL_REWRITE_RECOMMENDED": 90,
            "NEW_ARTICLE_RECOMMENDED": 85,
            "LOCAL_OPTIMIZATION": 70,
            "MINOR_REFRESH": 55,
            "FOLLOW_UP_REQUIRED": 45,
            "OBSERVE_ONLY": 30,
            "HEALTHY": 10,
        }[final]
        return max(0, min(100, round(base * 0.7 + risk_score * 0.2 + confidence * 0.1)))

    @classmethod
    def _latest_assessments(cls, medical_record):
        return {
            field: (
                medical_record.get(field, [])[-1]
                if medical_record.get(field) else None
            )
            for field in cls.ASSESSMENT_FIELDS
        }

    @staticmethod
    def _latest_vital_score(medical_record):
        scores = [
            item for item in medical_record.get("vital_scores", [])
            if item.get("overall_score") is not None
        ]
        return int(scores[-1]["overall_score"]) if scores else None

    @staticmethod
    def _latest_vital_score_id(medical_record):
        scores = medical_record.get("vital_scores", [])
        return scores[-1].get("score_id") if scores else None

    @staticmethod
    def _vital_sign_score(medical_record, code):
        if not medical_record.get("vital_profiles"):
            return None
        for item in medical_record["vital_profiles"][-1].get("signs", []):
            if item.get("code") == code and item.get("score") is not None:
                return int(round(item["score"]))
        return None

    @staticmethod
    def _dedupe(items):
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
