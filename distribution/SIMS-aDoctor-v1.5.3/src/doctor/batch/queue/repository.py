from __future__ import annotations

from copy import deepcopy
from typing import Protocol, Any


class BatchQueueRepository(Protocol):
    def create(self, record: dict[str, Any]) -> dict[str, Any]:
        ...

    def get(self, queue_record_id: str) -> dict[str, Any] | None:
        ...

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        ...

    def list_incomplete(self) -> list[dict[str, Any]]:
        ...


class InMemoryBatchQueueRepository:
    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}

    def create(self, record: dict[str, Any]) -> dict[str, Any]:
        key = record["queue_record_id"]
        if key in self._records:
            raise ValueError(f"Queue record already exists: {key}")
        self._records[key] = deepcopy(record)
        return deepcopy(record)

    def get(self, queue_record_id: str) -> dict[str, Any] | None:
        record = self._records.get(queue_record_id)
        return deepcopy(record) if record else None

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        key = record["queue_record_id"]
        if key not in self._records:
            raise KeyError(key)
        self._records[key] = deepcopy(record)
        return deepcopy(record)

    def list_incomplete(self) -> list[dict[str, Any]]:
        terminal = {"COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED", "CANCELLED"}
        return [
            deepcopy(record)
            for record in self._records.values()
            if record["status"] not in terminal
        ]
