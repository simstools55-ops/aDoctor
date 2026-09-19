from __future__ import annotations

from typing import Protocol

from .models import SearchAnalyticsRequest, SearchAnalyticsResponse


class SearchConsoleProviderError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class SearchConsoleProvider(Protocol):
    def query(self, request: SearchAnalyticsRequest) -> SearchAnalyticsResponse:
        ...
