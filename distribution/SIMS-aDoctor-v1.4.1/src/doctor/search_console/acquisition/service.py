from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import time
from typing import Any, Callable

from .models import SearchAnalyticsRequest, SearchAnalyticsRow
from .provider import SearchConsoleProvider, SearchConsoleProviderError


class AcquisitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class _PeriodResult:
    name: str
    start_date: date
    end_date: date
    row: SearchAnalyticsRow | None
    error_code: str | None = None
    error_message: str | None = None


class SearchConsoleAcquisitionService:
    def __init__(
        self,
        provider: SearchConsoleProvider,
        policy: dict[str, Any],
        *,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.provider = provider
        self.policy = policy
        self.sleep = sleep

    def acquire(
        self,
        *,
        case_id: str,
        site_id: str,
        article_id: str,
        site_url: str,
        page_url: str,
        requested_at: datetime | None = None,
        today: date | None = None,
    ) -> dict[str, Any]:
        requested = requested_at or datetime.now(timezone.utc)
        current_day = today or requested.date()
        lag_days = int(self.policy["date_policy"]["end_date_lag_days"])
        end_date = current_day - timedelta(days=lag_days)

        period_results: list[_PeriodResult] = []
        for name, days in self.policy["periods"].items():
            start_date = end_date - timedelta(days=int(days) - 1)
            try:
                response = self._query_with_retry(
                    SearchAnalyticsRequest(
                        site_url=site_url,
                        page_url=page_url,
                        start_date=start_date,
                        end_date=end_date,
                        dimensions=(),
                        row_limit=1,
                    )
                )
                row = response.rows[0] if response.rows else None
                period_results.append(_PeriodResult(name, start_date, end_date, row))
            except SearchConsoleProviderError as exc:
                period_results.append(
                    _PeriodResult(name, start_date, end_date, None, exc.code, exc.message)
                )

        query_rows: list[SearchAnalyticsRow] = []
        query_error: SearchConsoleProviderError | None = None
        try:
            query_rows = self._acquire_queries(
                site_url=site_url,
                page_url=page_url,
                start_date=end_date - timedelta(days=27),
                end_date=end_date,
            )
        except SearchConsoleProviderError as exc:
            query_error = exc

        status = self._status(period_results, query_error, query_rows)
        completed = datetime.now(timezone.utc)
        failed = [x for x in period_results if x.error_code]
        if query_error:
            failed.append(
                _PeriodResult("queries", end_date - timedelta(days=27), end_date, None,
                              query_error.code, query_error.message)
            )

        periods = {
            item.name: self._period_payload(item)
            for item in period_results
        }

        coverage_start = end_date - timedelta(days=self.policy["coverage_days"] - 1)
        error_code = failed[0].error_code if status == "FAILED" and failed else None
        error_message = failed[0].error_message if status == "FAILED" and failed else None

        return {
            "contract_name": "SIMS_DOCTOR_SEARCH_CONSOLE_OBSERVATION_INPUT_V1",
            "contract_version": "1.0",
            "case_id": case_id,
            "article": {
                "site_id": site_id,
                "article_id": article_id,
                "url": page_url,
            },
            "retrieval": {
                "requested_at": requested.isoformat(),
                "completed_at": completed.isoformat(),
                "status": status,
                "coverage_start": coverage_start.isoformat(),
                "coverage_end": end_date.isoformat(),
                "missing_days": [],
                "error_code": error_code,
                "error_message": error_message,
                "component_errors": [
                    {
                        "component": item.name,
                        "code": item.error_code,
                        "message": item.error_message,
                    }
                    for item in failed
                ],
            },
            "periods": periods,
            "queries": [
                {
                    "query": item.keys[0] if item.keys else "",
                    "clicks": item.clicks,
                    "impressions": item.impressions,
                    "ctr": item.ctr,
                    "position": item.position,
                }
                for item in query_rows
                if item.keys and item.keys[0]
            ],
        }

    def _query_with_retry(self, request: SearchAnalyticsRequest):
        retry = self.policy["retry"]
        maximum = int(retry["maximum_attempts"])
        retryable = set(retry["retryable_errors"])
        last_error: SearchConsoleProviderError | None = None
        for attempt in range(1, maximum + 1):
            try:
                return self.provider.query(request)
            except SearchConsoleProviderError as exc:
                last_error = exc
                if exc.code not in retryable or attempt == maximum:
                    raise
                self.sleep(float(attempt))
        raise last_error or AcquisitionError("Search Console request failed")

    def _acquire_queries(
        self,
        *,
        site_url: str,
        page_url: str,
        start_date: date,
        end_date: date,
    ) -> list[SearchAnalyticsRow]:
        settings = self.policy["query_rows"]
        page_size = int(settings["page_size"])
        maximum = int(settings["maximum_rows"])
        rows: list[SearchAnalyticsRow] = []
        start_row = 0

        while start_row < maximum:
            response = self._query_with_retry(
                SearchAnalyticsRequest(
                    site_url=site_url,
                    page_url=page_url,
                    start_date=start_date,
                    end_date=end_date,
                    dimensions=("query",),
                    row_limit=min(page_size, maximum - start_row),
                    start_row=start_row,
                )
            )
            page = list(response.rows)
            rows.extend(page)
            if len(page) < page_size:
                break
            start_row += len(page)

        rows.sort(key=lambda x: (-x.clicks, -x.impressions, x.keys))
        return rows[:maximum]

    @staticmethod
    def _period_payload(result: _PeriodResult) -> dict[str, Any]:
        row = result.row
        return {
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "clicks": row.clicks if row else 0,
            "impressions": row.impressions if row else 0,
            "ctr": row.ctr if row else 0,
            "position": row.position if row else None,
        }

    @staticmethod
    def _status(
        periods: list[_PeriodResult],
        query_error: SearchConsoleProviderError | None,
        query_rows: list[SearchAnalyticsRow],
    ) -> str:
        failures = sum(1 for x in periods if x.error_code) + (1 if query_error else 0)
        total = len(periods) + 1
        if failures == total:
            return "FAILED"
        if failures:
            return "PARTIAL"
        any_data = any(x.row and (x.row.clicks or x.row.impressions) for x in periods) or bool(query_rows)
        return "COMPLETE" if any_data else "NO_DATA"
