from __future__ import annotations

from typing import Any


class DoctorReportGenerator:
    """Generate action-first treatment plans for users and full traces for systems."""

    def __init__(self, policy: dict[str, Any]) -> None:
        self.labels = policy["labels"]

    def generate(self, medical_record, composite, recommendation, *, audience):
        if audience not in {"USER", "SYSTEM"}:
            raise ValueError("Unsupported report audience")

        patient = medical_record.get("patient", {})
        final = composite["final_diagnosis"]
        label = self.labels.get(final, final)
        target = recommendation["referral_target"]
        priority = recommendation["priority"]
        confidence = int(composite.get("confidence") or 0)

        article = {
            "site_id": patient.get("site_id"),
            "article_id": patient.get("article_id"),
            "url": patient.get("article_url") or patient.get("url"),
            "title": patient.get("article_title") or patient.get("title"),
        }
        treatment_class = self._treatment_class(target, recommendation)
        summary = self._summary(label, target, priority)
        diagnosis = {
            "code": final,
            "label": label,
            "confidence": confidence,
            "confidence_label": self._confidence_label(confidence),
            "severity": composite["severity"],
            "priority": composite["priority"],
        }
        recommendation_view = {
            "referral_target": target,
            "treatment_mode": recommendation["treatment_mode"],
            "treatment_class": treatment_class,
            "recommended_scope": recommendation["recommended_scope"],
            "prohibited_actions": recommendation["prohibited_actions"],
        }

        sections = [
            {
                "code": "DOCTOR_COMMENT",
                "title": "Doctorコメント",
                "content": self._doctor_comment(
                    label, target, treatment_class, confidence
                ),
            },
            {
                "code": "OVERALL_PLAN",
                "title": "総合診断",
                "content": {
                    "診断": label,
                    "診断確信度": f"{confidence}%（{self._confidence_label(confidence)}）",
                    "治療区分": treatment_class,
                    "次の担当": self._next_owner(target),
                },
            },
            {
                "code": "TODO",
                "title": "今回やること",
                "content": self._todo(target, treatment_class, recommendation),
            },
            {
                "code": "DO_NOT_DO",
                "title": "今回はやらないこと",
                "content": recommendation.get("prohibited_actions", []),
            },
            {
                "code": "WHY",
                "title": "この方針にした理由",
                "content": list(composite.get("reasons", [])),
            },
            {
                "code": "ADVICE",
                "title": "利用者へのアドバイス",
                "content": self._advice(final, target),
            },
            {
                "code": "HANDOFF_REQUEST",
                "title": "担当製品へ渡す依頼文",
                "content": self._handoff_request(target, recommendation, article),
            },
            {
                "code": "SBM_NEXT",
                "title": "SBMで行うこと",
                "content": self._sbm_next(target),
            },
            {
                "code": "MONITORING",
                "title": "次回診察予定",
                "content": recommendation["monitoring"],
            },
        ]

        trace = {
            "composite_diagnosis_id": composite["composite_diagnosis_id"],
            "treatment_recommendation_id": recommendation["recommendation_id"],
            "medical_record_event_count": len(medical_record.get("events", [])),
        }
        if audience == "SYSTEM":
            trace["supporting_assessments"] = composite.get(
                "supporting_assessments", []
            )
            trace["referral_request"] = recommendation.get("referral_request")
            sections.append(
                {
                    "code": "SYSTEM_TRACE",
                    "title": "System Trace",
                    "content": {
                        "supporting_assessments": composite.get(
                            "supporting_assessments", []
                        ),
                        "safety": composite.get("safety", {}),
                    },
                }
            )

        return {
            "audience": audience,
            "article": article,
            "summary": summary,
            "diagnosis": diagnosis,
            "recommendation": recommendation_view,
            "monitoring": recommendation["monitoring"],
            "sections": sections,
            "trace": trace,
        }

    @staticmethod
    def _confidence_label(confidence: int) -> str:
        if confidence >= 95:
            return "ほぼ確定"
        if confidence >= 80:
            return "可能性が高い"
        if confidence >= 60:
            return "有力な推定"
        if confidence >= 40:
            return "追加証拠が望ましい"
        return "診断保留"

    @classmethod
    def _doctor_comment(
        cls, label: str, target: str, treatment_class: str, confidence: int
    ) -> str:
        if confidence >= 80:
            certainty = (
                f"利用できる証拠から、{label}の可能性が高いと判断しました"
                f"（確信度{confidence}%）。"
            )
        elif confidence >= 60:
            certainty = (
                f"利用できる証拠から、{label}が有力だと推定しました"
                f"（確信度{confidence}%）。"
            )
        else:
            certainty = (
                f"現時点では証拠が十分ではないため、{label}を仮診断として扱います"
                f"（確信度{confidence}%）。"
            )

        if target in {"OBSERVE", "FOLLOW_UP", "NONE"}:
            reassurance = (
                "慌てて大きく書き直す段階ではありません。"
                "今は記事を守りながら経過を見る方が賢明です。"
            )
        elif treatment_class in {"軽微修正", "限定修正"}:
            reassurance = (
                "記事全体に重大な問題があるわけではありません。"
                "安全な範囲だけ整え、結果を見て次の治療を判断しましょう。"
            )
        else:
            reassurance = (
                "必要な範囲は明確になっています。"
                "変更範囲を守って処置すれば、不要な悪化リスクを抑えられます。"
            )

        return f"{certainty}\n\n{reassurance}"

    @classmethod
    def _todo(cls, target, treatment_class, recommendation):
        monitoring = recommendation.get("monitoring", {})
        if target in {"WRITER", "CREATOR", "MERGE"}:
            return {
                "今日": (
                    f"下のコピー用依頼文を{target.title()}へ渡し、"
                    f"{treatment_class}を依頼する"
                ),
                "処置後": "担当製品が返す処置結果JSONをSBMへ登録する",
                "次回": monitoring,
            }
        if target in {"OBSERVE", "FOLLOW_UP", "NONE"}:
            return {
                "今日": "記事を大きく変更せず、現状を維持する",
                "SBM": "経過観察と次回診察予定を管理する",
                "次回": monitoring,
            }
        return {
            "今日": "Doctorが示した確認事項だけを実施する",
            "確認後": "結果別の次の行動に従う",
            "次回": monitoring,
        }

    @classmethod
    def _advice(cls, final, target):
        text = str(final).upper()
        if any(k in text for k in ["UPDATE", "CORE", "SITE", "ALGORITHM"]):
            return (
                "記事単体よりサイト全体の評価変動が主因と考えられます。"
                "この場合は全面リライトを急がず、事実更新や明確に関連する内部リンクなど"
                "低リスクの整備を行い、SBMでサイト全体の回復傾向を観察するのが賢明です。"
            )
        if any(k in text for k in ["COMPET", "SERP"]):
            return (
                "記事品質を壊さず、競合との差が明確になる情報だけを追加してください。"
                "全面的な書き直しより、限定的な差別化の方が安全です。"
            )
        if any(k in text for k in ["LOW_SAMPLE", "INSUFFICIENT"]):
            return (
                "データが少ない時期の大幅変更は、改善効果を判定しにくくします。"
                "明確な事実修正だけ行い、十分な測定期間を確保してください。"
            )
        if target in {"OBSERVE", "FOLLOW_UP", "NONE"}:
            return (
                "今は変更しないことも適切な治療です。"
                "SBMで測定を続け、次回診察で方針を見直してください。"
            )
        return (
            "Doctorが許可した範囲だけを処置し、禁止範囲には触れないでください。"
            "処置後はSBMで効果測定を開始します。"
        )

    @classmethod
    def _handoff_request(cls, target, recommendation, article):
        if target in {"NONE", "OBSERVE", "FOLLOW_UP", "SBM"}:
            return None

        scope = recommendation.get("recommended_scope", [])
        prohibited = recommendation.get("prohibited_actions", [])
        dependencies = recommendation.get("dependencies", [])
        scope_text = "\n".join(f"・{item}" for item in scope) or (
            "・診断で許可された範囲のみ実施"
        )
        blocked_text = "\n".join(f"・{item}" for item in prohibited) or (
            "・診断範囲外の変更"
        )
        dependency_text = "\n".join(f"・{item}" for item in dependencies) or "・なし"
        product = target.title()

        return (
            f"下の本文をすべてコピーし、SIMS {product}へそのまま貼り付けてください。\n\n"
            f"【SIMS {product} 依頼】\n"
            f"CaseID: {recommendation.get('case_id') or ''}\n"
            f"ArticleID: {article.get('article_id') or ''}\n"
            f"URL: {article.get('url') or ''}\n"
            f"記事タイトル: {article.get('title') or ''}\n"
            f"治療区分: {cls._treatment_class(target, recommendation)}\n\n"
            f"実施範囲:\n{scope_text}\n\n"
            f"変更しないこと:\n{blocked_text}\n\n"
            f"前提条件:\n{dependency_text}\n\n"
            "処置完了後は、処置結果JSONをSBMへ登録できる形で返してください。"
        )

    @staticmethod
    def _sbm_next(target):
        if target in {"WRITER", "CREATOR", "MERGE"}:
            return (
                "担当製品の処置が終わった後、その製品が返す処置結果JSONを"
                "SBMへ登録してください。Doctor診断JSONは登録しません。"
            )
        return "SBMで経過観察、効果測定、次回診察予定を管理してください。"

    @staticmethod
    def _next_owner(target):
        if target in {"WRITER", "CREATOR", "MERGE"}:
            return target.title()
        if target in {"OBSERVE", "FOLLOW_UP", "NONE"}:
            return "SBM（経過観察）"
        return "利用者（指定された確認のみ）"

    @staticmethod
    def _treatment_class(target, recommendation):
        explicit = recommendation.get("treatment_class")
        if explicit:
            return explicit
        level = str(
            recommendation.get("treatment_level")
            or recommendation.get("treatment_mode")
            or recommendation.get("treatment_code")
            or ""
        ).upper()
        if target == "CREATOR":
            return "新規記事作成"
        if target == "MERGE":
            return "記事統合"
        if target in {"NONE", "OBSERVE", "FOLLOW_UP"}:
            return "経過観察"
        if any(k in level for k in ["FULL", "MAJOR", "L4"]):
            return "全面リライト"
        if any(k in level for k in ["REWRITE", "L3"]):
            return "通常リライト"
        if any(k in level for k in ["LIMITED", "LOCAL", "L2"]):
            return "限定修正"
        return "軽微修正"

    @staticmethod
    def _summary(label, target, priority):
        if target == "NONE":
            return f"診断結果は「{label}」です。現在、治療は不要です。"
        if target == "OBSERVE":
            return f"診断結果は「{label}」です。優先度{priority}で経過観察します。"
        if target == "FOLLOW_UP":
            return f"診断結果は「{label}」です。追加データ取得後に再診します。"
        if target == "SBM":
            return (
                f"診断結果は「{label}」です。"
                f"指定された確認作業だけを優先度{priority}で実施します。"
            )
        return (
            f"診断結果は「{label}」です。"
            f"{target}への紹介を優先度{priority}で推奨します。"
        )
