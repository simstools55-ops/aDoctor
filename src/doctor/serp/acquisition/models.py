from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawSerpResult:
    position: int
    title: str
    url: str
    domain: str
    snippet: str = ""
    published_at: str | None = None
    updated_at: str | None = None
    authority_score: int | None = None
    intent_match: int | None = None


@dataclass(frozen=True)
class RawSerpResponse:
    results: tuple[RawSerpResult, ...]
    features: tuple[str, ...] = ()
    provider_request_id: str | None = None
