from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import AlgorithmImpactEngine


class AlgorithmImpactService:
    def __init__(self, *, engine: AlgorithmImpactEngine, event_log: MedicalRecordEventLog) -> None:
        self.engine = engine
        self.event_log = event_log

    def assess(self, medical_record: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if event.get("event_type") == "ALGORITHM_IMPACT_ASSESSED" and event.get("idempotency_key") == idempotency_key:
                return event["payload"]["algorithm_impact_assessment"]

        result = self.engine.assess(medical_record)
        occurred_at = datetime.fromisoformat(result["assessed_at"])
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        self.event_log.append(
            medical_record,
            event_type="ALGORITHM_IMPACT_ASSESSED",
            payload={"algorithm_impact_assessment": result},
            occurred_at=occurred_at,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("algorithm_impact_assessments", []).append(result)
        medical_record.setdefault("counters", {})["algorithm_impact_assessment_count"] = len(
            medical_record["algorithm_impact_assessments"]
        )
        medical_record["updated_at"] = result["assessed_at"]
        return result
