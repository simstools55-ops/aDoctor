from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sqlite3
from typing import Any


class SQLiteSecurityState:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                '''
                CREATE TABLE IF NOT EXISTS api_nonces (
                    client_id TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    PRIMARY KEY (client_id, nonce)
                );

                CREATE TABLE IF NOT EXISTS api_idempotency (
                    client_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    PRIMARY KEY (client_id, idempotency_key)
                );

                CREATE TABLE IF NOT EXISTS api_audit_log (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    client_id TEXT,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    event TEXT NOT NULL,
                    request_id TEXT
                );
                '''
            )

    def claim_nonce(self, client_id: str, nonce: str, *, ttl_seconds: int) -> bool:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM api_nonces WHERE expires_at <= ?",
                (now.isoformat(),),
            )
            try:
                connection.execute(
                    "INSERT INTO api_nonces (client_id, nonce, expires_at) VALUES (?, ?, ?)",
                    (client_id, nonce, expires_at.isoformat()),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def get_idempotency(self, client_id: str, key: str) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc)
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM api_idempotency WHERE expires_at <= ?",
                (now.isoformat(),),
            )
            row = connection.execute(
                '''
                SELECT response_json
                FROM api_idempotency
                WHERE client_id = ? AND idempotency_key = ?
                ''',
                (client_id, key),
            ).fetchone()
        return json.loads(row["response_json"]) if row else None

    def put_idempotency(
        self,
        client_id: str,
        key: str,
        response: dict[str, Any],
        *,
        ttl_hours: int,
    ) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        payload = json.dumps(response, ensure_ascii=False, sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO api_idempotency (
                    client_id, idempotency_key, expires_at, response_json
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(client_id, idempotency_key)
                DO UPDATE SET expires_at = excluded.expires_at,
                              response_json = excluded.response_json
                ''',
                (client_id, key, expires_at.isoformat(), payload),
            )

    def append_audit(
        self,
        *,
        client_id: str | None,
        method: str,
        path: str,
        status_code: int,
        event: str,
        request_id: str | None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO api_audit_log (
                    occurred_at, client_id, method, path,
                    status_code, event, request_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    datetime.now(timezone.utc).isoformat(),
                    client_id,
                    method,
                    path,
                    status_code,
                    event,
                    request_id,
                ),
            )

    def audit_entries(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT occurred_at, client_id, method, path,
                       status_code, event, request_id
                FROM api_audit_log
                ORDER BY audit_id
                '''
            ).fetchall()
        return [dict(row) for row in rows]

    def ping(self) -> bool:
        with self._connect() as connection:
            return connection.execute("SELECT 1").fetchone()[0] == 1
