from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import VitalScoreEngine


def _score_id(now):
    return f"VSC-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class VitalScoreService:
    def __init__(
        self,
        *,
        engine: VitalScoreEngine,
        event_log: MedicalRecordEventLog,
    ) -> None:
        self.engine = engine
        self.event_log = event_log

    def calculate(
        self,
        medical_record: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "VITAL_SCORE_CALCULATED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["vital_score"]

        now = datetime.now(timezone.utc)
        calculated = self.engine.calculate(medical_record)
        result = {
            "contract_name": "SIMS_DOCTOR_VITAL_SCORE_RESULT_V1",
            "contract_version": "1.0",
            "score_id": _score_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "calculated_at": now.isoformat(),
            **calculated,
        }
        self.event_log.append(
            medical_record,
            event_type="VITAL_SCORE_CALCULATED",
            payload={"vital_score": result},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("vital_scores", []).append(result)
        medical_record.setdefault("counters", {})["vital_score_count"] = len(
            medical_record["vital_scores"]
        )
        medical_record["updated_at"] = now.isoformat()
        return result
