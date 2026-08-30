from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import CompositeDiagnosisEngine


def _diagnosis_id(now):
    return f"CDX-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class CompositeDiagnosisService:
    def __init__(
        self,
        *,
        engine: CompositeDiagnosisEngine,
        event_log: MedicalRecordEventLog,
    ) -> None:
        self.engine = engine
        self.event_log = event_log

    def diagnose(
        self,
        medical_record: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "COMPOSITE_DIAGNOSIS_COMPLETED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["composite_diagnosis"]

        now = datetime.now(timezone.utc)
        result = {
            "contract_name": "SIMS_DOCTOR_COMPOSITE_DIAGNOSIS_V1",
            "contract_version": "1.0",
            "composite_diagnosis_id": _diagnosis_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "diagnosed_at": now.isoformat(),
            **self.engine.diagnose(medical_record),
        }
        self.event_log.append(
            medical_record,
            event_type="COMPOSITE_DIAGNOSIS_COMPLETED",
            payload={"composite_diagnosis": result},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("composite_diagnoses", []).append(result)
        medical_record.setdefault("counters", {})[
            "composite_diagnosis_count"
        ] = len(medical_record["composite_diagnoses"])
        medical_record["updated_at"] = now.isoformat()
        return result
