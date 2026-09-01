from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any


class SQLiteSbmImportLedger:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS sbm_result_imports (
                    site_id TEXT NOT NULL,
                    batch_request_id TEXT NOT NULL,
                    result_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    imported_items INTEGER NOT NULL,
                    failed_items INTEGER NOT NULL,
                    PRIMARY KEY (site_id, batch_request_id, result_fingerprint)
                )
                '''
            )

    def acknowledge(
        self,
        package: dict[str, Any],
        *,
        imported_items: int,
        failed_items: int = 0,
    ) -> dict[str, Any]:
        site_id = package["site_id"]
        batch_request_id = package["batch_request_id"]
        fingerprint = package["result_fingerprint"]
        now = datetime.now(timezone.utc).isoformat()
        status = "PARTIAL" if failed_items else "IMPORTED"

        with self._connect() as connection:
            existing = connection.execute(
                '''
                SELECT status, imported_at, imported_items, failed_items
                FROM sbm_result_imports
                WHERE site_id = ? AND batch_request_id = ? AND result_fingerprint = ?
                ''',
                (site_id, batch_request_id, fingerprint),
            ).fetchone()
            if existing:
                return self._ack(
                    site_id, batch_request_id, fingerprint,
                    "ALREADY_IMPORTED", existing["imported_at"],
                    existing["imported_items"], existing["failed_items"]
                )
            connection.execute(
                '''
                INSERT INTO sbm_result_imports (
                    site_id, batch_request_id, result_fingerprint,
                    status, imported_at, imported_items, failed_items
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    site_id, batch_request_id, fingerprint,
                    status, now, imported_items, failed_items
                ),
            )
        return self._ack(
            site_id, batch_request_id, fingerprint,
            status, now, imported_items, failed_items
        )

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    @staticmethod
    def _ack(site_id, batch_request_id, fingerprint, status, imported_at,
             imported_items, failed_items):
        return {
            "contract_name": "SIMS_SBM_DOCTOR_BATCH_IMPORT_ACK_V1",
            "contract_version": "1.0",
            "site_id": site_id,
            "batch_request_id": batch_request_id,
            "result_fingerprint": fingerprint,
            "status": status,
            "imported_at": imported_at,
            "imported_items": int(imported_items),
            "failed_items": int(failed_items),
        }
