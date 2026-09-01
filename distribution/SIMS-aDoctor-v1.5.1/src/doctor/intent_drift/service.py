from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import IntentDriftEngine


def _assessment_id(now):
    return f"IDA-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class IntentDriftService:
    def __init__(
        self,
        *,
        engine: IntentDriftEngine,
        event_log: MedicalRecordEventLog,
    ) -> None:
        self.engine = engine
        self.event_log = event_log

    def assess(
        self,
        medical_record: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "INTENT_DRIFT_ASSESSED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["intent_drift_assessment"]

        now = datetime.now(timezone.utc)
        result = {
            "contract_name": "SIMS_DOCTOR_INTENT_DRIFT_ASSESSMENT_V1",
            "contract_version": "1.0",
            "assessment_id": _assessment_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "assessed_at": now.isoformat(),
            **self.engine.assess(medical_record),
        }
        self.event_log.append(
            medical_record,
            event_type="INTENT_DRIFT_ASSESSED",
            payload={"intent_drift_assessment": result},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("intent_drift_assessments", []).append(result)
        medical_record.setdefault("counters", {})[
            "intent_drift_assessment_count"
        ] = len(medical_record["intent_drift_assessments"])
        medical_record["updated_at"] = now.isoformat()
        return result
