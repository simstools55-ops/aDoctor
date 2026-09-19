from __future__ import annotations

from typing import Protocol

from .models import RawSerpResponse


class SerpProviderError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class SerpProvider(Protocol):
    def search(self, query: str, *, result_limit: int) -> RawSerpResponse:
        ...
