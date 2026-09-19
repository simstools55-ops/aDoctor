from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any, Dict, Optional


class InMemoryMedicalRecordRepository:
    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    def get(self, medical_record_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            value = self._records.get(medical_record_id)
            return deepcopy(value) if value else None

    def save(self, record: Dict[str, Any]) -> None:
        with self._lock:
            self._records[record["medical_record_id"]] = deepcopy(record)

    def delete(self, medical_record_id: str) -> None:
        with self._lock:
            self._records.pop(medical_record_id, None)
