from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SerpResult:
    position: int
    title: str
    url: str
    domain: str
    snippet: str
    published_at: str | None = None
    updated_at: str | None = None
    authority_score: int | None = None
    intent_match: int | None = None


@dataclass(frozen=True)
class SerpObservationInput:
    case_id: str
    site_id: str
    article_id: str
    article_url: str
    query: str
    requested_at: datetime
    completed_at: datetime
    status: str
    intent_primary: str
    intent_confidence: int
    intent_signals: tuple[str, ...]
    features: tuple[str, ...]
    results: tuple[SerpResult, ...]
    competition: dict[str, int]
    comparison: dict[str, Any] | None
    error_code: str | None = None
    error_message: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SerpObservationInput":
        article = data["article"]
        retrieval = data["retrieval"]
        intent = data["intent"]
        results = tuple(
            SerpResult(
                position=int(item["position"]),
                title=item["title"],
                url=item["url"],
                domain=item["domain"],
                snippet=item["snippet"],
                published_at=item.get("published_at"),
                updated_at=item.get("updated_at"),
                authority_score=item.get("authority_score"),
                intent_match=item.get("intent_match"),
            )
            for item in data["results"]
        )
        instance = cls(
            case_id=data["case_id"],
            site_id=article["site_id"],
            article_id=article["article_id"],
            article_url=article["url"],
            query=data["query"],
            requested_at=datetime.fromisoformat(retrieval["requested_at"]),
            completed_at=datetime.fromisoformat(retrieval["completed_at"]),
            status=retrieval["status"],
            intent_primary=intent["primary"],
            intent_confidence=int(intent["confidence"]),
            intent_signals=tuple(intent["signals"]),
            features=tuple(data["features"]),
            results=results,
            competition={key: int(value) for key, value in data["competition"].items()},
            comparison=data.get("comparison"),
            error_code=retrieval.get("error_code"),
            error_message=retrieval.get("error_message"),
        )
        instance.validate()
        return instance

    def validate(self) -> None:
        if self.status not in {"COMPLETE", "PARTIAL", "FAILED", "NO_DATA"}:
            raise ValueError("Unsupported SERP retrieval status")
        if not self.query.strip():
            raise ValueError("SERP query cannot be empty")
        if not 0 <= self.intent_confidence <= 100:
            raise ValueError("Intent confidence must be between 0 and 100")
        positions = [item.position for item in self.results]
        if positions != sorted(positions) or len(positions) != len(set(positions)):
            raise ValueError("SERP result positions must be unique and ordered")
        if self.status == "FAILED" and not self.error_code:
            raise ValueError("FAILED SERP retrieval requires error_code")
        for value in self.competition.values():
            if not 0 <= value <= 100:
                raise ValueError("Competition scores must be between 0 and 100")
