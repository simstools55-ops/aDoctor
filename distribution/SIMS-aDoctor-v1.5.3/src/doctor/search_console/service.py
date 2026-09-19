from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .models import SearchConsoleObservationInput


def _observation_id(now: datetime) -> str:
    return f"OBS-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class SearchConsoleObservationService:
    def __init__(self, event_log: MedicalRecordEventLog) -> None:
        self.event_log = event_log

    def record(
        self,
        medical_record: dict[str, Any],
        input_data: SearchConsoleObservationInput,
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        if medical_record["case_id"] != input_data.case_id:
            raise ValueError("Case ID mismatch")
        patient = medical_record["patient"]
        if patient["site_id"] != input_data.site_id:
            raise ValueError("Site ID mismatch")
        if patient["article_id"] != input_data.article_id:
            raise ValueError("Article ID mismatch")
        if patient["article_url"] != input_data.url:
            raise ValueError("Article URL mismatch")

        existing = self._find_by_idempotency_key(medical_record, idempotency_key)
        if existing is not None:
            return existing

        now = datetime.now(timezone.utc)
        observation = {
            "observation_id": _observation_id(now),
            "observation_type": "SEARCH_CONSOLE",
            "observed_at": input_data.completed_at.isoformat(),
            "source": "GOOGLE_SEARCH_CONSOLE",
            "schema_version": "1.0",
            "facts": self._facts(input_data),
        }

        event = self.event_log.append(
            medical_record,
            event_type="OBSERVATION_RECORDED",
            payload={
                "observation_id": observation["observation_id"],
                "observation_type": observation["observation_type"],
                "observation": observation,
            },
            occurred_at=now,
            idempotency_key=idempotency_key,
        )

        medical_record.setdefault("observations", []).append(observation)
        counters = medical_record.setdefault("counters", {})
        counters["observation_count"] = len(medical_record["observations"])
        medical_record["case_status"] = "OBSERVING"
        medical_record["updated_at"] = event.occurred_at.isoformat()
        return observation

    @staticmethod
    def _find_by_idempotency_key(
        medical_record: dict[str, Any], idempotency_key: str
    ) -> dict[str, Any] | None:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "OBSERVATION_RECORDED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["observation"]
        return None

    @staticmethod
    def _facts(input_data: SearchConsoleObservationInput) -> dict[str, Any]:
        return {
            "retrieval": {
                "requested_at": input_data.requested_at.isoformat(),
                "completed_at": input_data.completed_at.isoformat(),
                "status": input_data.status,
                "coverage_start": input_data.coverage_start.isoformat(),
                "coverage_end": input_data.coverage_end.isoformat(),
                "missing_days": [x.isoformat() for x in input_data.missing_days],
                "error_code": input_data.error_code,
                "error_message": input_data.error_message,
            },
            "periods": {
                name: {
                    "start_date": item.start_date.isoformat(),
                    "end_date": item.end_date.isoformat(),
                    "clicks": item.clicks,
                    "impressions": item.impressions,
                    "ctr": item.ctr,
                    "position": item.position,
                }
                for name, item in input_data.periods.items()
            },
            "queries": [
                {
                    "query": item.query,
                    "clicks": item.clicks,
                    "impressions": item.impressions,
                    "ctr": item.ctr,
                    "position": item.position,
                }
                for item in input_data.queries
            ],
        }
