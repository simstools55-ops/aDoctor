from __future__ import annotations

from typing import Any

from .models import SearchAnalyticsRequest, SearchAnalyticsResponse, SearchAnalyticsRow
from .provider import SearchConsoleProviderError


class GoogleSearchConsoleAdapter:
    def __init__(self, service: Any) -> None:
        self.service = service

    def query(self, request: SearchAnalyticsRequest) -> SearchAnalyticsResponse:
        body = {
            "startDate": request.start_date.isoformat(),
            "endDate": request.end_date.isoformat(),
            "dimensions": list(request.dimensions),
            "rowLimit": request.row_limit,
            "startRow": request.start_row,
            "dimensionFilterGroups": [{
                "filters": [{
                    "dimension": "page",
                    "operator": "equals",
                    "expression": request.page_url,
                }]
            }],
        }
        try:
            result = (
                self.service.searchanalytics()
                .query(siteUrl=request.site_url, body=body)
                .execute()
            )
        except Exception as exc:
            code = self._map_error(exc)
            raise SearchConsoleProviderError(code, str(exc)) from exc

        rows = tuple(SearchAnalyticsRow.from_mapping(item) for item in result.get("rows", []))
        return SearchAnalyticsResponse(rows=rows)

    @staticmethod
    def _map_error(exc: Exception) -> str:
        text = str(exc).lower()
        if "429" in text or "rate" in text:
            return "RATE_LIMIT"
        if "timeout" in text:
            return "TIMEOUT"
        if "503" in text or "temporar" in text:
            return "TEMPORARY_UNAVAILABLE"
        if "403" in text or "permission" in text:
            return "PERMISSION_DENIED"
        if "401" in text or "credential" in text:
            return "AUTHENTICATION_FAILED"
        return "PROVIDER_ERROR"
