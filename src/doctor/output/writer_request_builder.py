from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any


class WriterRequestError(ValueError):
    pass


GOALS = {
    "REWRITE_SNIPPET_AND_INTENT_ALIGNMENT": [
        "検索意図とSEOタイトル・メタディスクリプションを整合させる",
        "現在の上位クエリを損なわずCTR改善を目指す",
    ],
    "REWRITE_CONTENT_RECOVERY": [
        "順位低下の原因となる不足箇所を限定的に補う",
        "既存の強みと勝ちクエリを保護する",
    ],
    "REFRESH_OUTDATED_CONTENT": [
        "古い情報を公式情報で確認して更新する",
        "変更不要な本文や独自要素を維持する",
    ],
    "REASSESS_FAILED_TREATMENT": [
        "前回改善箇所と悪化データを比較する",
        "必要に応じて前回変更の修正または復元案を提示する",
    ],
    "REASSESS_INEFFECTIVE_IMPROVEMENT": [
        "前回変更と効果測定結果を比較して無効だった要因を特定する",
        "既存の強みを維持した別の改善案を提示する",
    ],
    "REVIEW_AND_ROLLBACK_WORSENING": [
        "悪化した指標と前回変更箇所の因果候補を確認する",
        "必要に応じて部分修正または復元のBefore/Afterを提示する",
    ],
}


def _request_id(now: datetime) -> str:
    return f"WRQ-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class WriterRequestBuilder:
    def build(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        diagnoses = medical_record.get("final_diagnoses", [])
        treatments = medical_record.get("treatment_recommendations", [])
        referrals = medical_record.get("referrals", [])
        if not diagnoses or not treatments or not referrals:
            raise WriterRequestError("Diagnosis, treatment recommendation, and referral are required")

        diagnosis = diagnoses[-1]
        treatment = treatments[-1]
        referral = referrals[-1]
        if diagnosis["status"] != "CONFIRMED":
            raise WriterRequestError("Deferred diagnosis cannot create a Writer request")
        if referral["target"] != "WRITER":
            raise WriterRequestError("Referral target is not Writer")

        now = datetime.now(timezone.utc)
        patient = medical_record["patient"]
        profiles = medical_record.get("vital_profiles", [])
        profile = profiles[-1] if profiles else None

        return {
            "contract_name": "SIMS_DOCTOR_WRITER_REQUEST_V1",
            "contract_version": "1.0",
            "request_id": _request_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "referral_id": referral["referral_id"],
            "article": {
                "site_id": patient["site_id"],
                "article_id": patient["article_id"],
                "url": patient["article_url"],
                "title": patient["article_title"],
            },
            "diagnosis": {
                "code": diagnosis["diagnosis_code"],
                "confidence": diagnosis["confidence"],
                "severity": diagnosis.get("severity"),
            },
            "treatment_directive": {
                "code": treatment["treatment_code"],
                "priority": treatment["priority"],
                "goals": GOALS.get(treatment["treatment_code"], ["診断結果に沿って限定的に改善する"]),
                "prohibited_actions": [
                    "診断範囲を超えた全面リライト",
                    "広告コードやアフィリエイトリンクの無断削除",
                    "既存の独自体験・口コミ・強みの無断削除",
                    "根拠のない数値や事実の追加",
                ],
            },
            "preservation": {
                "preserve_existing_strengths": True,
                "preserve_ads_and_links": True,
            },
            "trace": {
                "finding_ids": diagnosis.get("supporting_finding_ids", []),
                "evidence_ids": diagnosis.get("evidence_ids", []),
                "vital_profile_id": profile["profile_id"] if profile else None,
            },
            "created_at": now.isoformat(),
        }
