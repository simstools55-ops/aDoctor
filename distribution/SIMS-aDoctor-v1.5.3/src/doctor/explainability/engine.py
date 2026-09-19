from __future__ import annotations

from typing import Any


class ExplainableDiagnosisEngine:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def explain(
        self,
        medical_record: dict[str, Any],
        composite: dict[str, Any],
        recommendation: dict[str, Any],
        *,
        audience: str,
    ) -> dict[str, Any]:
        if audience not in {"USER", "SYSTEM"}:
            raise ValueError("Unsupported explanation audience")

        safety = composite.get("safety", {})
        path = []
        supporting = []
        blocking = []

        self._append_step(
            path,
            "DATA_SUFFICIENCY",
            not safety.get("low_sample_or_insufficient", False),
            "診断に必要なデータ量を確認しました。",
            "データ不足があるため確定判断を保留しました。",
        )
        self._append_step(
            path,
            "RECENT_CHANGE",
            not safety.get("recent_change_or_update", False),
            "直近変更による観察待ちはありません。",
            "直近変更後のため追加修正より観察を優先しました。",
        )
        self._append_step(
            path,
            "WINNER_QUERY",
            not safety.get("winner_query_protected", False),
            "Winner Query保護による制限はありません。",
            "Winner Queryを守るため大規模変更を制限しました。",
        )
        self._append_step(
            path,
            "MERGE",
            not safety.get("merge_required", False),
            "Merge優先条件はありません。",
            "カニバリ診断によりMergeを優先しました。",
        )

        for item in composite.get("supporting_assessments", []):
            factor = {
                "assessment_type": item.get("assessment_type"),
                "classification": item.get("classification"),
                "confidence": item.get("confidence"),
                "severity": item.get("severity"),
            }
            if audience == "SYSTEM":
                factor["assessment_id"] = item.get("assessment_id")
            supporting.append(factor)

        if safety.get("winner_query_protected"):
            blocking.append({
                "code": "WINNER_QUERY_PROTECTION",
                "message": "主要流入クエリを損なう変更は禁止されています。",
            })
        if safety.get("recent_change_or_update"):
            blocking.append({
                "code": "RECENT_CHANGE_OBSERVATION",
                "message": "変更直後のため再修正を避けます。",
            })
        if safety.get("low_sample_or_insufficient"):
            blocking.append({
                "code": "INSUFFICIENT_DATA",
                "message": "測定不足のため確定治療を避けます。",
            })

        path.append({
            "step": "FINAL_DIAGNOSIS",
            "status": "SELECTED",
            "message": (
                f"最終診断として{composite['final_diagnosis']}を選択しました。"
            ),
        })

        summary = self._summary(composite, recommendation)
        trace = {
            "composite_diagnosis_id": composite["composite_diagnosis_id"],
            "treatment_recommendation_id": recommendation["recommendation_id"],
        }
        if audience == "SYSTEM":
            trace["score"] = composite.get("score", {})
            trace["safety"] = safety
            trace["supporting_assessments"] = composite.get(
                "supporting_assessments", []
            )

        return {
            "audience": audience,
            "final_diagnosis": composite["final_diagnosis"],
            "summary": summary,
            "decision_path": path,
            "supporting_factors": supporting,
            "blocking_factors": blocking,
            "trace": trace,
        }

    @staticmethod
    def _append_step(path, code, passed, pass_message, block_message):
        path.append({
            "step": code,
            "status": "PASSED" if passed else "BLOCKED",
            "message": pass_message if passed else block_message,
        })

    @staticmethod
    def _summary(composite, recommendation):
        final = composite["final_diagnosis"]
        target = recommendation["referral_target"]
        if target == "NONE":
            return f"{final}と判断し、治療不要としました。"
        if target == "OBSERVE":
            return f"{final}と判断し、経過観察を選択しました。"
        if target == "FOLLOW_UP":
            return f"{final}と判断し、追加データ取得後の再診を選択しました。"
        return f"{final}と判断し、{target}への紹介を選択しました。"
