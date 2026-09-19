from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any


class ReferralFactory:
    def create(
        self,
        medical_record: dict[str, Any],
        recommendation: dict[str, Any],
        composite_diagnosis: dict[str, Any],
    ) -> dict[str, Any]:
        target = recommendation["referral_target"]
        now = datetime.now(timezone.utc)
        request_id = (
            f"REF-{now.strftime('%Y%m%d-%H%M%S')}-"
            f"{secrets.token_hex(3).upper()}"
        )
        patient = medical_record.get("patient", {})

        common = {
            "contract_version": "1.0",
            "request_id": request_id,
            "case_id": medical_record["case_id"],
            "article": {
                "site_id": patient.get("site_id"),
                "article_id": patient.get("article_id"),
                "url": (
                    patient.get("article_url")
                    or patient.get("url")
                ),
                "title": (
                    patient.get("article_title")
                    or patient.get("title")
                ),
            },
            "diagnosis": {
                "composite_diagnosis_id":
                    composite_diagnosis["composite_diagnosis_id"],
                "final_diagnosis":
                    composite_diagnosis["final_diagnosis"],
                "confidence": composite_diagnosis["confidence"],
                "priority": composite_diagnosis["priority"],
                "reasons": composite_diagnosis["reasons"],
            },
            "treatment": {
                "mode": recommendation["treatment_mode"],
                "scope": recommendation["recommended_scope"],
                "prohibited_actions":
                    recommendation["prohibited_actions"],
                "monitoring": recommendation["monitoring"],
            },
        }

        if target == "SIMS_WRITER":
            return {
                "contract_name": "SIMS_DOCTOR_WRITER_REQUEST_V1",
                **common,
            }
        if target == "SIMS_CREATOR":
            return {
                "contract_name": "SIMS_DOCTOR_CREATOR_REQUEST_V1",
                **common,
            }
        if target == "SIMS_MERGE":
            return {
                "contract_name": "SIMS_DOCTOR_MERGE_REQUEST_V1",
                **common,
            }
        return {
            "contract_name": "SIMS_DOCTOR_MONITORING_REQUEST_V1",
            **common,
            "monitoring_type": target,
        }
