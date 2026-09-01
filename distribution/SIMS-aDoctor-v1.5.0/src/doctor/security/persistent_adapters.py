from __future__ import annotations

from typing import Any

from .sqlite_store import SQLiteSecurityState


class SQLiteNonceStore:
    def __init__(self, state: SQLiteSecurityState) -> None:
        self.state = state

    def claim(self, client_id: str, nonce: str, *, ttl_seconds: int) -> bool:
        return self.state.claim_nonce(client_id, nonce, ttl_seconds=ttl_seconds)


class SQLiteIdempotencyStore:
    def __init__(self, state: SQLiteSecurityState) -> None:
        self.state = state

    def get(self, client_id: str, key: str) -> dict[str, Any] | None:
        return self.state.get_idempotency(client_id, key)

    def put(
        self,
        client_id: str,
        key: str,
        response: dict[str, Any],
        *,
        ttl_hours: int,
    ) -> None:
        self.state.put_idempotency(
            client_id, key, response, ttl_hours=ttl_hours
        )


class SQLiteAuditLog:
    def __init__(self, state: SQLiteSecurityState) -> None:
        self.state = state

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
        self.state.append_audit(
            client_id=client_id,
            method=method,
            path=path,
            status_code=status_code,
            event=event,
            request_id=request_id,
        )
