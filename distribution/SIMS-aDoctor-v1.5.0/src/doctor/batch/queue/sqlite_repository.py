from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import sqlite3
from typing import Any


class SQLiteBatchQueueRepository:
    """Durable SQLite implementation of the BatchQueueRepository protocol."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_queue_records (
                    queue_record_id TEXT PRIMARY KEY,
                    batch_request_id TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    record_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_batch_queue_status_updated "
                "ON batch_queue_records(status, updated_at)"
            )

    def create(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = self._serialize(record)
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO batch_queue_records "
                    "(queue_record_id, batch_request_id, status, updated_at, record_json) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        record["queue_record_id"], record["batch_request_id"],
                        record["status"], record["updated_at"], payload,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                f"Queue record already exists: {record['queue_record_id']}"
            ) from exc
        return deepcopy(record)

    def get(self, queue_record_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM batch_queue_records WHERE queue_record_id = ?",
                (queue_record_id,),
            ).fetchone()
        return json.loads(row["record_json"]) if row else None

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = self._serialize(record)
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE batch_queue_records SET status = ?, updated_at = ?, record_json = ? "
                "WHERE queue_record_id = ?",
                (
                    record["status"], record["updated_at"], payload,
                    record["queue_record_id"],
                ),
            )
            if cursor.rowcount != 1:
                raise KeyError(record["queue_record_id"])
        return deepcopy(record)

    def list_incomplete(self) -> list[dict[str, Any]]:
        terminal = ("COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED", "CANCELLED")
        placeholders = ",".join("?" for _ in terminal)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT record_json FROM batch_queue_records "
                f"WHERE status NOT IN ({placeholders}) ORDER BY updated_at ASC",
                terminal,
            ).fetchall()
        return [json.loads(row["record_json"]) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute(
                "SELECT COUNT(*) FROM batch_queue_records"
            ).fetchone()[0])

    @staticmethod
    def _serialize(record: dict[str, Any]) -> str:
        return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sqlite_repository_ping_placeholder():
    pass


def _ping(self) -> bool:
    with self._connect() as connection:
        return connection.execute("SELECT 1").fetchone()[0] == 1

SQLiteBatchQueueRepository.ping = _ping
