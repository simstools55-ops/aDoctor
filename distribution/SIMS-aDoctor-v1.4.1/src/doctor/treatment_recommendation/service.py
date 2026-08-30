from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import TreatmentRecommendationEngine
from .referral_factory import ReferralFactory


def _recommendation_id(now):
    return (
        f"TRX-{now.strftime('%Y%m%d-%H%M%S')}-"
        f"{secrets.token_hex(3).upper()}"
    )


class TreatmentRecommendationService:
    def __init__(
        self,
        *,
        engine: TreatmentRecommendationEngine,
        referral_factory: ReferralFactory,
        event_log: MedicalRecordEventLog,
    ) -> None:
        self.engine = engine
        self.referral_factory = referral_factory
        self.event_log = event_log

    def recommend(
        self,
        medical_record: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type")
                == "TREATMENT_RECOMMENDATION_CREATED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["treatment_recommendation"]

        composites = medical_record.get("composite_diagnoses", [])
        if not composites:
            raise ValueError(
                "Composite Diagnosis is required before treatment recommendation"
            )
        composite = composites[-1]
        now = datetime.now(timezone.utc)
        recommendation = {
            "contract_name":
                "SIMS_DOCTOR_TREATMENT_RECOMMENDATION_V1",
            "contract_version": "1.0",
            "recommendation_id": _recommendation_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "created_at": now.isoformat(),
            "source_composite_diagnosis_id":
                composite["composite_diagnosis_id"],
            **self.engine.recommend(medical_record, composite),
        }
        referral = self.referral_factory.create(
            medical_record,
            recommendation,
            composite,
        )
        recommendation["referral_request"] = referral

        self.event_log.append(
            medical_record,
            event_type="TREATMENT_RECOMMENDATION_CREATED",
            payload={"treatment_recommendation": recommendation},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault(
            "treatment_recommendations", []
        ).append(recommendation)
        medical_record.setdefault("counters", {})[
            "treatment_recommendation_count"
        ] = len(medical_record["treatment_recommendations"])
        medical_record["updated_at"] = now.isoformat()
        return recommendation
