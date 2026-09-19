from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import ExplainableDiagnosisEngine


def _explanation_id(now):
    return (
        f"EXP-{now.strftime('%Y%m%d-%H%M%S')}-"
        f"{secrets.token_hex(3).upper()}"
    )


class ExplainableDiagnosisService:
    def __init__(
        self,
        *,
        engine: ExplainableDiagnosisEngine,
        event_log: MedicalRecordEventLog,
    ) -> None:
        self.engine = engine
        self.event_log = event_log

    def create(
        self,
        medical_record: dict[str, Any],
        *,
        audience: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            explanation = event.get("payload", {}).get(
                "diagnosis_explanation", {}
            )
            if (
                event.get("event_type") == "DIAGNOSIS_EXPLANATION_CREATED"
                and event.get("idempotency_key") == idempotency_key
                and explanation.get("audience") == audience
            ):
                return explanation

        if not medical_record.get("composite_diagnoses"):
            raise ValueError("Composite Diagnosis is required")
        if not medical_record.get("treatment_recommendations"):
            raise ValueError("Treatment Recommendation is required")

        composite = medical_record["composite_diagnoses"][-1]
        recommendation = medical_record["treatment_recommendations"][-1]
        now = datetime.now(timezone.utc)
        result = {
            "contract_name": "SIMS_DOCTOR_EXPLANATION_V1",
            "contract_version": "1.0",
            "explanation_id": _explanation_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "created_at": now.isoformat(),
            **self.engine.explain(
                medical_record,
                composite,
                recommendation,
                audience=audience,
            ),
        }

        self.event_log.append(
            medical_record,
            event_type="DIAGNOSIS_EXPLANATION_CREATED",
            payload={"diagnosis_explanation": result},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("diagnosis_explanations", []).append(result)
        medical_record.setdefault("counters", {})[
            "diagnosis_explanation_count"
        ] = len(medical_record["diagnosis_explanations"])
        medical_record["updated_at"] = now.isoformat()
        return result
