from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class SearchConsolePeriod:
    start_date: date
    end_date: date
    clicks: float
    impressions: float
    ctr: float
    position: float | None


@dataclass(frozen=True)
class QueryMetric:
    query: str
    clicks: float
    impressions: float
    ctr: float
    position: float | None


@dataclass(frozen=True)
class SearchConsoleObservationInput:
    case_id: str
    site_id: str
    article_id: str
    url: str
    requested_at: datetime
    completed_at: datetime
    status: str
    coverage_start: date
    coverage_end: date
    periods: dict[str, SearchConsolePeriod]
    queries: tuple[QueryMetric, ...]
    missing_days: tuple[date, ...] = ()
    error_code: str | None = None
    error_message: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchConsoleObservationInput":
        retrieval = data["retrieval"]
        article = data["article"]

        def period(value: dict[str, Any]) -> SearchConsolePeriod:
            return SearchConsolePeriod(
                start_date=date.fromisoformat(value["start_date"]),
                end_date=date.fromisoformat(value["end_date"]),
                clicks=float(value["clicks"]),
                impressions=float(value["impressions"]),
                ctr=float(value["ctr"]),
                position=None if value["position"] is None else float(value["position"]),
            )

        periods = {name: period(value) for name, value in data["periods"].items()}
        queries = tuple(
            QueryMetric(
                query=item["query"],
                clicks=float(item["clicks"]),
                impressions=float(item["impressions"]),
                ctr=float(item["ctr"]),
                position=None if item["position"] is None else float(item["position"]),
            )
            for item in data["queries"]
        )

        instance = cls(
            case_id=data["case_id"],
            site_id=article["site_id"],
            article_id=article["article_id"],
            url=article["url"],
            requested_at=datetime.fromisoformat(retrieval["requested_at"]),
            completed_at=datetime.fromisoformat(retrieval["completed_at"]),
            status=retrieval["status"],
            coverage_start=date.fromisoformat(retrieval["coverage_start"]),
            coverage_end=date.fromisoformat(retrieval["coverage_end"]),
            periods=periods,
            queries=queries,
            missing_days=tuple(date.fromisoformat(x) for x in retrieval.get("missing_days", [])),
            error_code=retrieval.get("error_code"),
            error_message=retrieval.get("error_message"),
        )
        instance.validate()
        return instance

    def validate(self) -> None:
        if self.status not in {"COMPLETE", "PARTIAL", "FAILED", "NO_DATA"}:
            raise ValueError("Unsupported retrieval status")
        if self.coverage_end < self.coverage_start:
            raise ValueError("Coverage end precedes coverage start")
        if set(self.periods) != {"days_28", "days_90", "days_365"}:
            raise ValueError("28, 90, and 365 day periods are required")
        for item in self.periods.values():
            if not 0 <= item.ctr <= 1:
                raise ValueError("CTR must be between 0 and 1")
            if item.clicks < 0 or item.impressions < 0:
                raise ValueError("Metrics cannot be negative")
        for item in self.queries:
            if not item.query.strip():
                raise ValueError("Query cannot be empty")
            if not 0 <= item.ctr <= 1:
                raise ValueError("Query CTR must be between 0 and 1")
        if self.status == "FAILED" and not self.error_code:
            raise ValueError("FAILED retrieval requires error_code")
