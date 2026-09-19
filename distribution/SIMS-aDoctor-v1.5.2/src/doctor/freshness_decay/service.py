from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import FreshnessDecayEngine


def _assessment_id(now):
    return f"FDA-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class FreshnessDecayService:
    def __init__(
        self,
        *,
        engine: FreshnessDecayEngine,
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
                event.get("event_type") == "FRESHNESS_DECAY_ASSESSED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["freshness_decay_assessment"]

        now = datetime.now(timezone.utc)
        result = {
            "contract_name": "SIMS_DOCTOR_FRESHNESS_DECAY_ASSESSMENT_V1",
            "contract_version": "1.0",
            "assessment_id": _assessment_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "assessed_at": now.isoformat(),
            **self.engine.assess(medical_record),
        }
        self.event_log.append(
            medical_record,
            event_type="FRESHNESS_DECAY_ASSESSED",
            payload={"freshness_decay_assessment": result},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("freshness_decay_assessments", []).append(result)
        medical_record.setdefault("counters", {})[
            "freshness_decay_assessment_count"
        ] = len(medical_record["freshness_decay_assessments"])
        medical_record["updated_at"] = now.isoformat()
        return result
