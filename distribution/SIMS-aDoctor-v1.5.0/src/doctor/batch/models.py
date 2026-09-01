from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class BatchItem:
    item_id: str
    article_id: str
    url: str
    title: str
    request_payload: dict[str, Any]
    longitudinal_profile: dict[str, Any] | None = None
    current_metrics: dict[str, Any] | None = None


@dataclass(frozen=True)
class BatchRequest:
    batch_request_id: str
    requested_at: datetime
    site: dict[str, Any]
    items: tuple[BatchItem, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BatchRequest":
        items = tuple(
            BatchItem(
                item_id=item["item_id"],
                article_id=item["article_id"],
                url=item["url"],
                title=item["title"],
                request_payload=dict(item["request_payload"]),
                longitudinal_profile=(
                    dict(item["longitudinal_profile"])
                    if item.get("longitudinal_profile") else None
                ),
                current_metrics=(
                    dict(item["current_metrics"])
                    if item.get("current_metrics") else None
                ),
            )
            for item in data["items"]
        )
        instance = cls(
            batch_request_id=data["batch_request_id"],
            requested_at=datetime.fromisoformat(data["requested_at"]),
            site=dict(data["site"]),
            items=items,
        )
        instance.validate()
        return instance

    def validate(self) -> None:
        item_ids = [item.item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("Duplicate batch item ID")
        article_ids = [item.article_id for item in self.items]
        if len(article_ids) != len(set(article_ids)):
            raise ValueError("Duplicate article ID in batch")
        if not self.items:
            raise ValueError("Batch must contain at least one item")
