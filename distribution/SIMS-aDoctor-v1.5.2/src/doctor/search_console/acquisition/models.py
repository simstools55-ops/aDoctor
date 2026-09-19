from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class SearchAnalyticsRequest:
    site_url: str
    page_url: str
    start_date: date
    end_date: date
    dimensions: tuple[str, ...]
    row_limit: int
    start_row: int = 0


@dataclass(frozen=True)
class SearchAnalyticsRow:
    keys: tuple[str, ...]
    clicks: float
    impressions: float
    ctr: float
    position: float | None

    @classmethod
    def from_mapping(cls, item: dict[str, Any]) -> "SearchAnalyticsRow":
        return cls(
            keys=tuple(str(x) for x in item.get("keys", [])),
            clicks=float(item.get("clicks", 0)),
            impressions=float(item.get("impressions", 0)),
            ctr=float(item.get("ctr", 0)),
            position=None if item.get("position") is None else float(item["position"]),
        )


@dataclass(frozen=True)
class SearchAnalyticsResponse:
    rows: tuple[SearchAnalyticsRow, ...]
    request_id: str | None = None
