from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MedicalRecordEvent:
    event_id: str
    event_type: str
    occurred_at: datetime
    case_id: str
    medical_record_id: str
    sequence: int
    payload_hash: str
    payload: dict[str, Any]
    idempotency_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "case_id": self.case_id,
            "medical_record_id": self.medical_record_id,
            "sequence": self.sequence,
            "idempotency_key": self.idempotency_key,
            "payload_hash": self.payload_hash,
            "payload": self.payload,
        }
