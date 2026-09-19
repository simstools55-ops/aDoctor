from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CrossArticleObservationInput:
    case_id: str
    site_id: str
    primary_article: dict[str, Any]
    candidates: tuple[dict[str, Any], ...]
    observed_at: datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CrossArticleObservationInput":
        item = cls(
            case_id=data["case_id"],
            site_id=data["site_id"],
            primary_article=dict(data["primary_article"]),
            candidates=tuple(dict(x) for x in data["candidates"]),
            observed_at=datetime.fromisoformat(data["observed_at"]),
        )
        item.validate()
        return item

    def validate(self) -> None:
        primary_id = self.primary_article["article_id"]
        candidate_ids = [x["article"]["article_id"] for x in self.candidates]
        if primary_id in candidate_ids:
            raise ValueError("Primary article cannot appear as a candidate")
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("Duplicate candidate article ID")
        for candidate in self.candidates:
            for key in ("query_overlap_ratio", "title_similarity", "intent_similarity"):
                if not 0 <= candidate[key] <= 1:
                    raise ValueError(f"{key} must be between 0 and 1")
