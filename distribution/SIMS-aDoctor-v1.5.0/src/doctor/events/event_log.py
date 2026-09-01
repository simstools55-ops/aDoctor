from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any

from .models import MedicalRecordEvent


class EventLogError(ValueError):
    pass


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _event_id(now: datetime) -> str:
    return f"EVT-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class MedicalRecordEventLog:
    def __init__(self, allowed_event_types: set[str]) -> None:
        self.allowed_event_types = set(allowed_event_types)

    def append(
        self,
        medical_record: dict[str, Any],
        *,
        event_type: str,
        payload: dict[str, Any],
        occurred_at: datetime | None = None,
        idempotency_key: str | None = None,
    ) -> MedicalRecordEvent:
        if event_type not in self.allowed_event_types:
            raise EventLogError(f"Unknown event type: {event_type}")
        if not isinstance(payload, dict):
            raise EventLogError("Event payload must be an object")

        events = medical_record.setdefault("events", [])
        self.validate_existing(events)

        digest = _payload_hash(payload)

        if idempotency_key:
            for existing in events:
                if existing.get("idempotency_key") == idempotency_key:
                    if (
                        existing.get("event_type") == event_type
                        and existing.get("payload_hash") == digest
                    ):
                        return self._from_dict(existing)
                    raise EventLogError(
                        "Idempotency key already exists with different event content"
                    )

        now = occurred_at or datetime.now(timezone.utc)
        event = MedicalRecordEvent(
            event_id=_event_id(now),
            event_type=event_type,
            occurred_at=now,
            case_id=medical_record["case_id"],
            medical_record_id=medical_record["medical_record_id"],
            sequence=len(events) + 1,
            idempotency_key=idempotency_key,
            payload_hash=digest,
            payload=payload,
        )
        events.append(event.to_dict())
        medical_record["updated_at"] = now.isoformat()
        return event

    def validate_existing(self, events: list[dict[str, Any]]) -> None:
        seen_ids: set[str] = set()
        seen_keys: set[str] = set()
        for expected_sequence, event in enumerate(events, start=1):
            if event.get("sequence") != expected_sequence:
                raise EventLogError("Event sequence is not contiguous")
            event_id = event.get("event_id")
            if not event_id or event_id in seen_ids:
                raise EventLogError("Duplicate or missing event ID")
            seen_ids.add(event_id)
            key = event.get("idempotency_key")
            if key:
                if key in seen_keys:
                    raise EventLogError("Duplicate idempotency key")
                seen_keys.add(key)
            payload = event.get("payload")
            if not isinstance(payload, dict):
                raise EventLogError("Stored event payload must be an object")
            if event.get("payload_hash") != _payload_hash(payload):
                raise EventLogError("Stored event payload hash mismatch")

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> MedicalRecordEvent:
        return MedicalRecordEvent(
            event_id=data["event_id"],
            event_type=data["event_type"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            case_id=data["case_id"],
            medical_record_id=data["medical_record_id"],
            sequence=data["sequence"],
            idempotency_key=data.get("idempotency_key"),
            payload_hash=data["payload_hash"],
            payload=data["payload"],
        )
