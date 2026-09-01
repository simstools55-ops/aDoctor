from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], tuple[datetime, dict[str, Any]]] = {}

    def get(self, client_id: str, key: str) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc)
        record = self._records.get((client_id, key))
        if record is None:
            return None
        expires_at, response = record
        if expires_at <= now:
            del self._records[(client_id, key)]
            return None
        return dict(response)

    def put(
        self,
        client_id: str,
        key: str,
        response: dict[str, Any],
        *,
        ttl_hours: int,
    ) -> None:
        self._records[(client_id, key)] = (
            datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
            dict(response),
        )
