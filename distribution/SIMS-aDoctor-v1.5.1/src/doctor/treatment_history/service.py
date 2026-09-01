from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .models import TreatmentHistoryInput


def _observation_id(now: datetime) -> str:
    return f"OBS-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class TreatmentHistoryObservationService:
    def __init__(self, event_log: MedicalRecordEventLog) -> None:
        self.event_log = event_log

    def record(
        self,
        medical_record: dict[str, Any],
        input_data: TreatmentHistoryInput,
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "OBSERVATION_RECORDED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["observation"]

        if medical_record["case_id"] != input_data.case_id:
            raise ValueError("Case ID mismatch")
        patient = medical_record["patient"]
        if patient["site_id"] != input_data.site_id:
            raise ValueError("Site ID mismatch")
        if patient["article_id"] != input_data.article_id:
            raise ValueError("Article ID mismatch")
        if patient["article_url"] != input_data.article_url:
            raise ValueError("Article URL mismatch")

        now = datetime.now(timezone.utc)
        observation = {
            "observation_id": _observation_id(now),
            "observation_type": "TREATMENT_HISTORY",
            "observed_at": input_data.observed_at.isoformat(),
            "source": "SBM_IMPROVEMENT_HISTORY",
            "schema_version": "1.0",
            "facts": {
                "treatment": input_data.treatment,
                "baseline": input_data.baseline,
                "checkpoints": list(input_data.checkpoints),
                "assessment": input_data.assessment,
            },
        }
        self.event_log.append(
            medical_record,
            event_type="OBSERVATION_RECORDED",
            payload={
                "observation_id": observation["observation_id"],
                "observation_type": "TREATMENT_HISTORY",
                "observation": observation,
            },
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("observations", []).append(observation)
        medical_record.setdefault("history", []).append({
            "event_type": "TREATMENT_EFFECT_MEASURED",
            "treatment_id": input_data.treatment["treatment_id"],
            "observed_at": input_data.observed_at.isoformat(),
            "classification": input_data.assessment["classification"],
        })
        medical_record.setdefault("counters", {})["observation_count"] = len(
            medical_record["observations"]
        )
        medical_record["updated_at"] = now.isoformat()
        return observation
