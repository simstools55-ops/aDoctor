from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class LongTermObservationInput:
    case_id: str
    site_id: str
    article_id: str
    article_url: str
    observed_at: datetime
    windows: tuple[dict[str, Any], ...]
    trend: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LongTermObservationInput":
        article = data["article"]
        item = cls(
            case_id=data["case_id"],
            site_id=article["site_id"],
            article_id=article["article_id"],
            article_url=article["url"],
            observed_at=datetime.fromisoformat(data["observed_at"]),
            windows=tuple(dict(x) for x in data["windows"]),
            trend=dict(data["trend"]),
        )
        item.validate()
        return item

    def validate(self) -> None:
        if not self.windows:
            raise ValueError("At least one long-term window is required")
        dates = [item["start_date"] for item in self.windows]
        if dates != sorted(dates):
            raise ValueError("Long-term windows must be chronological")
        for item in self.windows:
            if not 0 <= item["ctr"] <= 1:
                raise ValueError("CTR must be between 0 and 1")
