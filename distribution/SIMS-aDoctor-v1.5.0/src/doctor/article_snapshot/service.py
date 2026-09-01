from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .models import ArticleSnapshotInput


def _observation_id(now: datetime) -> str:
    return f"OBS-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class ArticleSnapshotService:
    def __init__(self, event_log: MedicalRecordEventLog) -> None:
        self.event_log = event_log

    def record(
        self,
        medical_record: dict[str, Any],
        input_data: ArticleSnapshotInput,
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        existing = self._find_existing(medical_record, idempotency_key)
        if existing is not None:
            return existing

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
        previous = self._latest_snapshot(medical_record)
        comparison = input_data.comparison or self._compare(previous, input_data)

        observation = {
            "observation_id": _observation_id(now),
            "observation_type": "ARTICLE_SNAPSHOT",
            "observed_at": input_data.captured_at.isoformat(),
            "source": "ARTICLE_CONTENT",
            "schema_version": "1.0",
            "facts": {
                "title": input_data.title,
                "meta_description": input_data.meta_description,
                "published_at": input_data.published_at.isoformat() if input_data.published_at else None,
                "updated_at": input_data.updated_at.isoformat() if input_data.updated_at else None,
                "headings": list(input_data.headings),
                "faq_items": list(input_data.faq_items),
                "internal_links": list(input_data.internal_links),
                "metrics": input_data.metrics,
                "intent_alignment": input_data.intent_alignment,
                "freshness_markers": list(input_data.freshness_markers),
                "comparison": comparison,
            },
        }

        event = self.event_log.append(
            medical_record,
            event_type="OBSERVATION_RECORDED",
            payload={
                "observation_id": observation["observation_id"],
                "observation_type": "ARTICLE_SNAPSHOT",
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
    def _latest_snapshot(medical_record):
        matches = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") == "ARTICLE_SNAPSHOT"
        ]
        return matches[-1] if matches else None

    @staticmethod
    def _compare(previous, current):
        if previous is None:
            return None
        facts = previous["facts"]
        previous_headings = [item["text"] for item in facts.get("headings", [])]
        current_headings = [item["text"] for item in current.headings]
        previous_links = {item["url"] for item in facts.get("internal_links", [])}
        current_links = {item["url"] for item in current.internal_links}
        return {
            "previous_observation_id": previous["observation_id"],
            "title_changed": facts.get("title") != current.title,
            "added_headings": [item for item in current_headings if item not in previous_headings],
            "removed_headings": [item for item in previous_headings if item not in current_headings],
            "faq_count_change": len(current.faq_items) - len(facts.get("faq_items", [])),
            "added_internal_links": sorted(current_links - previous_links),
            "removed_internal_links": sorted(previous_links - current_links),
        }

    @staticmethod
    def _find_existing(medical_record, idempotency_key):
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "OBSERVATION_RECORDED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["observation"]
        return None
