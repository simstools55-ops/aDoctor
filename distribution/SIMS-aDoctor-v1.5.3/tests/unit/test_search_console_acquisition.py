from datetime import date, datetime, timezone
from pathlib import Path
import json

from src.doctor.search_console.acquisition import (
    SearchAnalyticsResponse,
    SearchAnalyticsRow,
    SearchConsoleAcquisitionService,
    SearchConsoleProviderError,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "knowledge/observation/search_console/acquisition_policy_v1.json")
    .read_text(encoding="utf-8")
)


class FakeProvider:
    def __init__(self):
        self.calls = []

    def query(self, request):
        self.calls.append(request)
        if request.dimensions == ("query",):
            return SearchAnalyticsResponse(rows=(
                SearchAnalyticsRow(("query a",), 10, 100, 0.1, 3.0),
                SearchAnalyticsRow(("query b",), 5, 200, 0.025, 8.0),
            ))
        days = (request.end_date - request.start_date).days + 1
        return SearchAnalyticsResponse(rows=(
            SearchAnalyticsRow((), float(days), float(days * 100), 0.01, 8.0),
        ))


def test_acquires_28_90_365_and_queries():
    provider = FakeProvider()
    service = SearchConsoleAcquisitionService(provider, POLICY, sleep=lambda _: None)
    result = service.acquire(
        case_id="CASE-1",
        site_id="site",
        article_id="A1",
        site_url="sc-domain:example.com",
        page_url="https://example.com/a",
        requested_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
        today=date(2026, 8, 4),
    )
    assert result["retrieval"]["status"] == "COMPLETE"
    assert result["periods"]["days_28"]["clicks"] == 28
    assert result["periods"]["days_90"]["clicks"] == 90
    assert result["periods"]["days_365"]["clicks"] == 365
    assert [x["query"] for x in result["queries"]] == ["query a", "query b"]
    assert result["retrieval"]["coverage_end"] == "2026-08-01"


class PartialProvider(FakeProvider):
    def query(self, request):
        if not request.dimensions and (request.end_date - request.start_date).days + 1 == 90:
            raise SearchConsoleProviderError("PERMISSION_DENIED", "denied")
        return super().query(request)


def test_partial_status_when_one_component_fails():
    service = SearchConsoleAcquisitionService(PartialProvider(), POLICY, sleep=lambda _: None)
    result = service.acquire(
        case_id="CASE-1",
        site_id="site",
        article_id="A1",
        site_url="sc-domain:example.com",
        page_url="https://example.com/a",
        today=date(2026, 8, 4),
    )
    assert result["retrieval"]["status"] == "PARTIAL"
    assert result["periods"]["days_90"]["impressions"] == 0
    assert result["retrieval"]["component_errors"][0]["component"] == "days_90"


class RetryProvider(FakeProvider):
    def __init__(self):
        super().__init__()
        self.failures = 0

    def query(self, request):
        if self.failures < 2:
            self.failures += 1
            raise SearchConsoleProviderError("RATE_LIMIT", "retry")
        return super().query(request)


def test_retryable_errors_are_retried():
    provider = RetryProvider()
    service = SearchConsoleAcquisitionService(provider, POLICY, sleep=lambda _: None)
    result = service.acquire(
        case_id="CASE-1",
        site_id="site",
        article_id="A1",
        site_url="sc-domain:example.com",
        page_url="https://example.com/a",
        today=date(2026, 8, 4),
    )
    assert result["retrieval"]["status"] == "COMPLETE"
    assert provider.failures == 2
