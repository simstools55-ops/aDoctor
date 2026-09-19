from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TreatmentHistoryInput:
    case_id: str
    site_id: str
    article_id: str
    article_url: str
    treatment: dict[str, Any]
    baseline: dict[str, Any]
    checkpoints: tuple[dict[str, Any], ...]
    observed_at: datetime
    assessment: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TreatmentHistoryInput":
        article = data["article"]
        item = cls(
            case_id=data["case_id"],
            site_id=article["site_id"],
            article_id=article["article_id"],
            article_url=article["url"],
            treatment=dict(data["treatment"]),
            baseline=dict(data["baseline"]),
            checkpoints=tuple(dict(x) for x in data["checkpoints"]),
            observed_at=datetime.fromisoformat(data["observed_at"]),
            assessment=dict(data["assessment"]),
        )
        item.validate()
        return item

    def validate(self) -> None:
        days = [item["days_after_treatment"] for item in self.checkpoints]
        if days != sorted(days) or len(days) != len(set(days)):
            raise ValueError("Treatment checkpoints must be unique and chronological")
        for measurement in (self.baseline, *self.checkpoints):
            if not 0 <= measurement["ctr"] <= 1:
                raise ValueError("CTR must be between 0 and 1")
        selected = self.assessment["selected_checkpoint_days"]
        if selected not in days:
            raise ValueError("Selected checkpoint is not present")
