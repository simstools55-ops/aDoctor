from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class InMemoryAuditLog:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def append(
        self,
        *,
        client_id: str | None,
        method: str,
        path: str,
        status_code: int,
        event: str,
        request_id: str | None = None,
    ) -> None:
        self.entries.append({
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "client_id": client_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "event": event,
            "request_id": request_id,
        })
