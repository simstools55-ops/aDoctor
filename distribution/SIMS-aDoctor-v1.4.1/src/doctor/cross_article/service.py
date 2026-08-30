from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .models import CrossArticleObservationInput


def _observation_id(now: datetime) -> str:
    return f"OBS-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class CrossArticleObservationService:
    def __init__(self, event_log: MedicalRecordEventLog) -> None:
        self.event_log = event_log

    def record(
        self,
        medical_record: dict[str, Any],
        input_data: CrossArticleObservationInput,
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
        if medical_record["patient"]["site_id"] != input_data.site_id:
            raise ValueError("Site ID mismatch")
        if medical_record["patient"]["article_id"] != input_data.primary_article["article_id"]:
            raise ValueError("Primary article mismatch")

        now = datetime.now(timezone.utc)
        observation = {
            "observation_id": _observation_id(now),
            "observation_type": "CROSS_ARTICLE",
            "observed_at": input_data.observed_at.isoformat(),
            "source": "ARTICLE_CATALOG_AND_SEARCH_CONSOLE",
            "schema_version": "1.0",
            "facts": {
                "primary_article": input_data.primary_article,
                "candidates": list(input_data.candidates),
            },
        }

        self.event_log.append(
            medical_record,
            event_type="OBSERVATION_RECORDED",
            payload={
                "observation_id": observation["observation_id"],
                "observation_type": "CROSS_ARTICLE",
                "observation": observation,
            },
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("observations", []).append(observation)
        medical_record.setdefault("counters", {})["observation_count"] = len(
            medical_record["observations"]
        )
        medical_record["updated_at"] = now.isoformat()
        return observation
