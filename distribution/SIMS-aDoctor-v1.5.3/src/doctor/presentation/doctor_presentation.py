from __future__ import annotations

from typing import Any


_INTERNAL_TOKENS = (
    "contract", "schema", "allowed_scope", "blocked_scope", "handoff_mode",
    "evidence_id", "confidence_percent", "actions_permitted", "actions_prohibited",
)


class DoctorPresentationBuilder:
    """Project Doctor machine result into a human-facing presentation.

    This builder intentionally hides contract/routing/scope field names and
    exposes only information needed for the user to act.
    """

    def build(
        self,
        *,
        diagnosis: dict[str, Any] | None,
        recommendation: dict[str, Any] | None,
        destination: str,
        treatment_required: bool,
        review_days: int | None,
    ) -> dict[str, Any]:
        diagnosis = diagnosis or {}
        recommendation = recommendation or {}

        summary = (
            diagnosis.get("summary")
            or diagnosis.get("rationale")
            or self._fallback_summary(diagnosis)
        )
        strategy = str(recommendation.get("strategy") or "").upper()

        do_now = self._do_now(recommendation, destination, treatment_required, strategy)
        do_not = self._do_not(recommendation, treatment_required, strategy)
        next_step = self._next_step(destination, treatment_required, review_days, strategy)
        note = recommendation.get("reassurance_comment") or recommendation.get("strategy_reason")

        payload = {
            "standard": "SIMS_PRESENTATION_STANDARD_V1",
            "summary": self._clean(summary),
            "do_now": [self._clean(x) for x in do_now if self._clean(x)],
            "do_not": [self._clean(x) for x in do_not if self._clean(x)],
            "next_step": self._clean(next_step),
            "review_after_days": review_days,
            "note": self._clean(note),
        }
        return payload

    @staticmethod
    def _fallback_summary(diagnosis: dict[str, Any]) -> str:
        status = str(diagnosis.get("status") or "").upper()
        if status == "DEFERRED":
            return "現時点では診断を確定せず、追加データを確認して再診します。"
        if status == "CONFIRMED":
            return "診断結果に基づいて、必要な処置だけを進めます。"
        return "現在の状態を確認し、次の対応方針を整理しました。"

    @staticmethod
    def _do_now(
        recommendation: dict[str, Any],
        destination: str,
        treatment_required: bool,
        strategy: str,
    ) -> list[str]:
        if strategy == "WAIT" or not treatment_required:
            todo = recommendation.get("user_todo") or []
            instructions = [
                str(item.get("instruction"))
                for item in todo
                if isinstance(item, dict) and item.get("instruction")
            ]
            return instructions or ["記事を大きく変更せず、指定期間まで経過を観察します。"]

        scope = recommendation.get("recommended_scope") or recommendation.get("scope") or []
        if scope:
            return [f"{item}を、診断で許可された範囲だけ修正します。" for item in scope]

        if destination == "SIMS_WRITER":
            return ["SBMが生成するWriter紹介状に従い、必要な箇所だけ修正します。"]
        if destination == "SIMS_CREATOR":
            return ["SBMが生成するCreator紹介状に従い、新記事作成を進めます。"]
        if destination == "SIMS_MERGE":
            return ["SBMが生成するMerge紹介状に従い、統合設計を進めます。"]
        return ["SBMが生成する次の紹介状に従って対応します。"]

    @staticmethod
    def _do_not(
        recommendation: dict[str, Any],
        treatment_required: bool,
        strategy: str,
    ) -> list[str]:
        prohibited = recommendation.get("prohibited_actions") or []
        humanized = []
        mapping = {
            "FULL_REWRITE": "今回は全面リライトを行いません。",
            "AGGRESSIVE_TITLE_CHANGE": "検索流入を大きく変えるタイトル改変は行いません。",
            "AUTOMATIC_DELETE": "記事を自動で削除しません。",
            "AUTOMATIC_NOINDEX": "記事を自動でnoindexにしません。",
            "AUTOMATIC_REDIRECT": "URL転送を自動で実施しません。",
            "AUTOMATIC_PUBLICATION": "変更を自動公開しません。",
            "MERGE_EXECUTION": "今回は記事統合を実行しません。",
            "NEW_ARTICLE_CREATION": "今回は新記事を作成しません。",
        }
        for item in prohibited:
            text = mapping.get(str(item))
            if text and text not in humanized:
                humanized.append(text)
        if strategy == "WAIT" and "今回は全面リライトを行いません。" not in humanized:
            humanized.insert(0, "今回は全面リライトを行いません。")
        if not treatment_required and not humanized:
            humanized.append("現時点では大きな変更を行いません。")
        return humanized[:5]

    @staticmethod
    def _next_step(destination: str, treatment_required: bool, review_days: int | None, strategy: str) -> str:
        if strategy == "WAIT" or not treatment_required:
            if review_days:
                return f"{review_days}日後を目安にSBMで再確認してください。"
            return "SBMで経過を確認し、必要になった時点で再診してください。"
        if destination == "SIMS_WRITER":
            return "この診断結果をSBMへ登録し、SBMが生成したWriter紹介状で修正を進めてください。"
        if destination == "SIMS_CREATOR":
            return "この診断結果をSBMへ登録し、SBMが生成したCreator紹介状で新記事作成を進めてください。"
        if destination == "SIMS_MERGE":
            return "この診断結果をSBMへ登録し、SBMが生成したMerge紹介状で統合検討を進めてください。"
        return "この診断結果をSBMへ登録し、表示された次の作業を進めてください。"

    @staticmethod
    def _clean(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        lowered = text.lower()
        # Presentation must never explain adapter/contract internals.
        if any(token in lowered for token in _INTERNAL_TOKENS):
            return "内部処理はSBMが自動で引き継ぎます。"
        return text
