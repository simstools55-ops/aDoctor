from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.doctor.reporting import DiagnosisReportBuilder
from .case_result_v2 import CaseResultV2Builder


class SingleCaseResultBuilder:
    def __init__(self, report_builder: DiagnosisReportBuilder | None = None) -> None:
        self.report_builder = report_builder or DiagnosisReportBuilder()

    def build(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        patient = medical_record["patient"]
        diagnoses = medical_record.get("final_diagnoses", [])
        diagnosis = diagnoses[-1] if diagnoses else None
        treatments = medical_record.get("treatment_recommendations", [])
        treatment = treatments[-1] if treatments else None
        referrals = medical_record.get("referrals", [])
        referral = referrals[-1] if referrals else None
        runs = medical_record.get("pipeline_runs", [])
        pipeline = runs[-1] if runs else None
        profiles = medical_record.get("vital_profiles", [])
        profile = profiles[-1] if profiles else None

        if diagnosis is None:
            result_status = "FAILED"
            diagnosis_payload = {
                "status": "FAILED",
                "code": None,
                "confidence": None,
                "severity": None,
                "defer_reason": "NO_DIAGNOSIS_RECORD",
            }
            review = {"recommended_review_days": None, "review_due_at": None}
        else:
            result_status = "DIAGNOSED" if diagnosis["status"] == "CONFIRMED" else "FOLLOW_UP"
            diagnosis_payload = {
                "status": diagnosis["status"],
                "code": diagnosis.get("diagnosis_code"),
                "confidence": diagnosis.get("confidence"),
                "severity": diagnosis.get("severity"),
                "defer_reason": diagnosis.get("defer_reason"),
            }
            review = {
                "recommended_review_days": diagnosis.get("recommended_review_days"),
                "review_due_at": diagnosis.get("review_due_at"),
            }

        legacy = {
            "contract_name": "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1",
            "contract_version": "1.0",
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "article": {
                "site_id": patient["site_id"],
                "article_id": patient["article_id"],
                "url": patient["article_url"],
                "title": patient["article_title"],
            },
            "result_status": result_status,
            "diagnosis": diagnosis_payload,
            "treatment": (
                {
                    "code": treatment["treatment_code"],
                    "target": treatment["target"],
                    "priority": treatment["priority"],
                }
                if treatment else None
            ),
            "referral": (
                {"referral_id": referral["referral_id"], "target": referral["target"]}
                if referral else None
            ),
            "review": review,
            "user_display": self.report_builder.build(medical_record),
            "trace": {
                "pipeline_run_id": pipeline["pipeline_run_id"] if pipeline else None,
                "diagnosis_id": diagnosis["diagnosis_id"] if diagnosis else None,
                "finding_ids": diagnosis.get("supporting_finding_ids", []) if diagnosis else [],
                "evidence_ids": diagnosis.get("evidence_ids", []) if diagnosis else [],
                "vital_profile_id": profile["profile_id"] if profile else None,
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        result = CaseResultV2Builder().build(medical_record, user_display=legacy["user_display"])
        result.update({
            "result_status": legacy["result_status"],
            "treatment": legacy["treatment"],
            "review": legacy["review"],
            "trace": legacy["trace"],
            "legacy_result": legacy,
        })
        return result
