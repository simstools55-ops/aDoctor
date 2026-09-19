from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from typing import Any, Dict, Iterable, Optional


ACTIVE_STATUSES = {
    "OPEN", "REQUEST_VALIDATED", "RECORD_CREATED", "READY_FOR_OBSERVATION",
    "OBSERVING", "DIAGNOSING", "DIAGNOSED", "REFERRED",
    "UNDER_TREATMENT", "FOLLOW_UP",
}


@dataclass(frozen=True)
class CaseLookup:
    case: Optional[Dict[str, Any]]
    reused: bool


class InMemoryCaseRegistry:
    """Reference registry for Sprint2-2 and deterministic tests.

    Persistent adapters can implement the same public methods later.
    """

    def __init__(self) -> None:
        self._cases: Dict[str, Dict[str, Any]] = {}
        self._sequences: Dict[str, int] = {}
        self._lock = RLock()

    def next_case_sequence(self, date_key: str) -> int:
        with self._lock:
            current = self._sequences.get(date_key, 0) + 1
            self._sequences[date_key] = current
            return current

    def find_active(self, site_id: str, article_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            matches = [
                case for case in self._cases.values()
                if case["site_id"] == site_id
                and case["article_id"] == article_id
                and case["case_status"] in ACTIVE_STATUSES
            ]
            if not matches:
                return None
            latest = max(matches, key=lambda item: item["updated_at"])
            return deepcopy(latest)

    def get(self, case_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            value = self._cases.get(case_id)
            return deepcopy(value) if value else None

    def save(self, case: Dict[str, Any]) -> None:
        with self._lock:
            self._cases[case["case_id"]] = deepcopy(case)

    def delete(self, case_id: str) -> None:
        with self._lock:
            self._cases.pop(case_id, None)

    def all(self) -> Iterable[Dict[str, Any]]:
        with self._lock:
            return [deepcopy(item) for item in self._cases.values()]
