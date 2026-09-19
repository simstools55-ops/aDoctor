from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import LongTermDegradationEngine


def _assessment_id(now):
    return f"LDA-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class LongTermDegradationService:
    def __init__(
        self,
        *,
        engine: LongTermDegradationEngine,
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
                event.get("event_type") == "LONG_TERM_DEGRADATION_ASSESSED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["long_term_degradation_assessment"]

        now = datetime.now(timezone.utc)
        assessed = self.engine.assess(medical_record)
        result = {
            "contract_name":
                "SIMS_DOCTOR_LONG_TERM_DEGRADATION_ASSESSMENT_V1",
            "contract_version": "1.0",
            "assessment_id": _assessment_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "assessed_at": now.isoformat(),
            **assessed,
        }
        self.event_log.append(
            medical_record,
            event_type="LONG_TERM_DEGRADATION_ASSESSED",
            payload={"long_term_degradation_assessment": result},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault(
            "long_term_degradation_assessments", []
        ).append(result)
        medical_record.setdefault("counters", {})[
            "long_term_degradation_assessment_count"
        ] = len(medical_record["long_term_degradation_assessments"])
        medical_record["updated_at"] = now.isoformat()
        return result
