from __future__ import annotations

from datetime import datetime, timedelta, timezone


class InMemoryNonceStore:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], datetime] = {}

    def claim(self, client_id: str, nonce: str, *, ttl_seconds: int) -> bool:
        now = datetime.now(timezone.utc)
        self._purge(now)
        key = (client_id, nonce)
        if key in self._values:
            return False
        self._values[key] = now + timedelta(seconds=ttl_seconds)
        return True

    def _purge(self, now: datetime) -> None:
        expired = [key for key, expires_at in self._values.items() if expires_at <= now]
        for key in expired:
            del self._values[key]
