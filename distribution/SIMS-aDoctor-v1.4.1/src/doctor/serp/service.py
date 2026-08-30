from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .models import SerpObservationInput


def _observation_id(now: datetime) -> str:
    return f"OBS-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class SerpObservationService:
    def __init__(self, event_log: MedicalRecordEventLog) -> None:
        self.event_log = event_log

    def record(
        self,
        medical_record: dict[str, Any],
        input_data: SerpObservationInput,
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
        if patient["article_url"] != input_data.article_url:
            raise ValueError("Article URL mismatch")

        existing = self._find_existing(medical_record, idempotency_key)
        if existing is not None:
            return existing

        now = datetime.now(timezone.utc)
        observation = {
            "observation_id": _observation_id(now),
            "observation_type": "SERP",
            "observed_at": input_data.completed_at.isoformat(),
            "source": "SERP_PROVIDER",
            "schema_version": "1.0",
            "facts": {
                "query": input_data.query,
                "retrieval": {
                    "requested_at": input_data.requested_at.isoformat(),
                    "completed_at": input_data.completed_at.isoformat(),
                    "status": input_data.status,
                    "error_code": input_data.error_code,
                    "error_message": input_data.error_message,
                },
                "intent": {
                    "primary": input_data.intent_primary,
                    "confidence": input_data.intent_confidence,
                    "signals": list(input_data.intent_signals),
                },
                "features": list(input_data.features),
                "results": [
                    {
                        "position": item.position,
                        "title": item.title,
                        "url": item.url,
                        "domain": item.domain,
                        "snippet": item.snippet,
                        "published_at": item.published_at,
                        "updated_at": item.updated_at,
                        "authority_score": item.authority_score,
                        "intent_match": item.intent_match,
                    }
                    for item in input_data.results
                ],
                "competition": input_data.competition,
                "comparison": input_data.comparison,
            },
        }

        event = self.event_log.append(
            medical_record,
            event_type="OBSERVATION_RECORDED",
            payload={
                "observation_id": observation["observation_id"],
                "observation_type": "SERP",
                "observation": observation,
            },
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("observations", []).append(observation)
        medical_record.setdefault("counters", {})["observation_count"] = len(
            medical_record["observations"]
        )
        medical_record["case_status"] = "OBSERVING"
        medical_record["updated_at"] = event.occurred_at.isoformat()
        return observation

    @staticmethod
    def _find_existing(medical_record, idempotency_key):
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "OBSERVATION_RECORDED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["observation"]
        return None
