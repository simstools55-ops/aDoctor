from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ArticleSnapshotInput:
    case_id: str
    site_id: str
    article_id: str
    article_url: str
    captured_at: datetime
    published_at: datetime | None
    updated_at: datetime | None
    title: str
    meta_description: str | None
    headings: tuple[dict[str, Any], ...]
    faq_items: tuple[dict[str, Any], ...]
    internal_links: tuple[dict[str, Any], ...]
    metrics: dict[str, int]
    intent_alignment: dict[str, Any]
    freshness_markers: tuple[str, ...]
    comparison: dict[str, Any] | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArticleSnapshotInput":
        article = data["article"]
        instance = cls(
            case_id=data["case_id"],
            site_id=article["site_id"],
            article_id=article["article_id"],
            article_url=article["url"],
            captured_at=datetime.fromisoformat(data["captured_at"]),
            published_at=datetime.fromisoformat(article["published_at"]) if article.get("published_at") else None,
            updated_at=datetime.fromisoformat(article["updated_at"]) if article.get("updated_at") else None,
            title=data["title"],
            meta_description=data.get("meta_description"),
            headings=tuple(data["headings"]),
            faq_items=tuple(data["faq_items"]),
            internal_links=tuple(data["internal_links"]),
            metrics={key: int(value) for key, value in data["metrics"].items()},
            intent_alignment=dict(data["intent_alignment"]),
            freshness_markers=tuple(data.get("freshness_markers", [])),
            comparison=data.get("comparison"),
        )
        instance.validate()
        return instance

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("Article title cannot be empty")
        orders = [item["order"] for item in self.headings]
        if orders != sorted(orders) or len(orders) != len(set(orders)):
            raise ValueError("Heading order must be unique and ordered")
        if self.metrics["heading_count"] != len(self.headings):
            raise ValueError("heading_count does not match headings")
        if self.metrics["faq_count"] != len(self.faq_items):
            raise ValueError("faq_count does not match faq_items")
        if self.metrics["internal_link_count"] != len(self.internal_links):
            raise ValueError("internal_link_count does not match internal_links")
        if not 0 <= int(self.intent_alignment["score"]) <= 100:
            raise ValueError("Intent alignment score must be between 0 and 100")
