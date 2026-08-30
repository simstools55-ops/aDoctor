from __future__ import annotations

from typing import Any


class TreatmentRecommendationEngine:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def recommend(
        self,
        medical_record: dict[str, Any],
        composite_diagnosis: dict[str, Any],
    ) -> dict[str, Any]:
        final = composite_diagnosis["final_diagnosis"]
        mapping = self.policy["mapping"][final]
        target = mapping["target"]
        mode = mapping["treatment_mode"]
        scope = list(mapping["scope"])
        safety = dict(composite_diagnosis.get("safety", {}))
        reasons = list(composite_diagnosis.get("reasons", []))
        algorithm = composite_diagnosis.get("algorithm_assessment") or {}
        strategy = self._strategy(final, target, mode, safety, algorithm)

        if strategy == "WAIT":
            target = "OBSERVE"
            mode = "OBSERVATION"
            scope = ["MONITORING"]
            reasons.insert(0, "Googleアップデート展開中の外部変動を考慮し、現時点の治療を保留します。")

        if target == "SIMS_CREATOR" and not safety.get("new_article_allowed"):
            target = "FOLLOW_UP"
            mode = "FOLLOW_UP"
            scope = ["ADDITIONAL_DATA", "REASSESSMENT"]
            reasons.insert(0, "新記事作成の安全条件を満たしていないため再診へ変更しました。")

        if mode == "FULL_REWRITE" and not safety.get("full_rewrite_allowed"):
            target = "SIMS_WRITER"
            mode = "LOCAL_OPTIMIZATION"
            scope = [
                "SEO_TITLE", "META_DESCRIPTION",
                "INTRODUCTION", "HEADINGS", "FAQ"
            ]
            reasons.insert(0, "大規模リライト禁止条件により局所改善へ制限しました。")

        if final == "MERGE_RECOMMENDED" and target != "SIMS_MERGE":
            target = "SIMS_MERGE"
            mode = "MERGE_REVIEW"

        prohibited = [
            "AUTOMATIC_DELETE",
            "AUTOMATIC_NOINDEX",
            "AUTOMATIC_REDIRECT",
            "AUTOMATIC_PUBLICATION",
        ]
        if safety.get("winner_query_protected"):
            prohibited.extend([
                "REMOVE_WINNER_QUERY",
                "AGGRESSIVE_TITLE_CHANGE",
                "FULL_REWRITE",
            ])
        if target != "SIMS_MERGE":
            prohibited.append("MERGE_EXECUTION")
        if target != "SIMS_CREATOR":
            prohibited.append("NEW_ARTICLE_CREATION")

        monitoring = self._monitoring(final, target)
        reasons.insert(
            0,
            f"Composite Diagnosisの{final}を{target}向け紹介へ変換しました。"
        )

        return {
            "referral_target": target,
            "treatment_mode": mode,
            "strategy": strategy,
            "strategy_reason": self._strategy_reason(strategy, algorithm, final),
            "priority": int(composite_diagnosis.get("priority", 0)),
            "recommended_scope": scope,
            "prohibited_actions": sorted(set(prohibited)),
            "reasons": self._dedupe(reasons),
            "monitoring": monitoring,
            "wait_plan": self._wait_plan(strategy),
            "user_todo": self._user_todo(strategy),
            "reassurance_comment": self._reassurance_comment(strategy, algorithm),
            "safety": {
                "doctor_executes_treatment": False,
                "winner_query_protected": bool(
                    safety.get("winner_query_protected")
                ),
                "new_article_allowed": bool(
                    safety.get("new_article_allowed")
                ),
                "full_rewrite_allowed": bool(
                    safety.get("full_rewrite_allowed")
                ),
                "merge_required": bool(safety.get("merge_required")),
            },
            "trace": {
                "composite_diagnosis_id":
                    composite_diagnosis["composite_diagnosis_id"],
                "supporting_assessment_ids": [
                    item.get("assessment_id")
                    for item in composite_diagnosis.get(
                        "supporting_assessments", []
                    )
                    if item.get("assessment_id")
                ],
            },
        }


    @staticmethod
    def _strategy(final, target, mode, safety, algorithm):
        if safety.get("algorithm_wait_recommended"):
            return "WAIT"
        if target in {"SIMS_CREATOR", "SIMS_MERGE"}:
            return None
        if final in {"HEALTHY", "OBSERVE_ONLY", "FOLLOW_UP_REQUIRED"}:
            return "WAIT"
        if final == "MINOR_REFRESH":
            return "LIGHT_FIX"
        if final == "LOCAL_OPTIMIZATION":
            return "NORMAL_REWRITE"
        if final == "FULL_REWRITE_RECOMMENDED" or mode == "FULL_REWRITE":
            return "FULL_REWRITE"
        return "LIGHT_FIX"

    @staticmethod
    def _strategy_reason(strategy, algorithm, final):
        if strategy == "WAIT" and algorithm.get("status") in {"LIKELY", "HIGH"}:
            return "Googleアップデート影響がLIKELY/HIGHで、展開中のため待機を優先します。"
        mapping = {
            "WAIT": "経過観察または追加Evidenceを優先します。",
            "LIGHT_FIX": "限定的な更新で対応可能な診断です。",
            "NORMAL_REWRITE": "通常範囲のリライトが妥当です。",
            "FULL_REWRITE": "複数領域の重大問題により全面リライトが妥当です。",
        }
        return mapping.get(strategy)

    def _wait_plan(self, strategy):
        if strategy != "WAIT":
            return None
        policy = self.policy.get("wait_policy") or {}
        return {
            "reason": "ALGORITHM_OR_CLINICAL_OBSERVATION",
            "minimum_wait_days": int(policy.get("minimum_wait_days", 7)),
            "recommended_review_days": int(policy.get("recommended_review_days", 14)),
            "observe": ["CLICKS", "IMPRESSIONS", "CTR", "POSITION", "QUERY_DISTRIBUTION", "SERP_COMPOSITION"],
            "avoid": ["FULL_REWRITE"],
        }

    @staticmethod
    def _user_todo(strategy):
        if strategy == "WAIT":
            return [{
                "order": 1,
                "action": "WAIT",
                "instruction": "記事本文を大きく変更せず、指定期間後に再診してください。",
                "required": True,
            }]
        if strategy:
            return [{
                "order": 1,
                "action": strategy,
                "instruction": "SBMが生成する紹介状に従って処置してください。",
                "required": True,
            }]
        return []

    @staticmethod
    def _reassurance_comment(strategy, algorithm):
        if strategy != "WAIT":
            return None
        if algorithm.get("status") in {"LIKELY", "HIGH"}:
            return (
                "公式アップデート情報と複数Evidenceの一致が確認されています。"
                "対象記事だけの問題と断定せず、展開中は大規模変更を避けて再診する方が安全です。"
            )
        return "現時点では大規模変更より経過観察または追加Evidenceの取得を優先します。"

    @staticmethod
    def _monitoring(final, target):
        if final == "HEALTHY":
            return {
                "required": False,
                "recommended_days": None,
                "metrics": [],
            }
        if target == "OBSERVE":
            return {
                "required": True,
                "recommended_days": 28,
                "metrics": ["CLICKS", "IMPRESSIONS", "CTR", "POSITION"],
            }
        if target == "FOLLOW_UP":
            return {
                "required": True,
                "recommended_days": 14,
                "metrics": ["DATA_COMPLETENESS", "CLICKS", "IMPRESSIONS"],
            }
        return {
            "required": True,
            "recommended_days": 28,
            "metrics": [
                "CLICKS", "IMPRESSIONS", "CTR",
                "POSITION", "VITAL_SCORE"
            ],
        }

    @staticmethod
    def _dedupe(items):
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
