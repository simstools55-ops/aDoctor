from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class VitalSignResult:
    code: str
    status: str
    score: int | None
    classification: str | None
    confidence: int
    calculated_at: datetime
    evidence_ids: tuple[str, ...]
    source_observation_ids: tuple[str, ...]
    formula_version: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "status": self.status,
            "score": self.score,
            "classification": self.classification,
            "confidence": self.confidence,
            "calculated_at": self.calculated_at.isoformat(),
            "evidence_ids": list(self.evidence_ids),
            "source_observation_ids": list(self.source_observation_ids),
            "formula_version": self.formula_version,
            "details": self.details,
        }


@dataclass(frozen=True)
class VitalProfile:
    profile_id: str
    calculated_at: datetime
    source_observation_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    signs: tuple[VitalSignResult, ...]
    overall_score: int | None
    overall_classification: str | None
    available_count: int
    unavailable_count: int
    formula_set_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "calculated_at": self.calculated_at.isoformat(),
            "source_observation_ids": list(self.source_observation_ids),
            "evidence_ids": list(self.evidence_ids),
            "signs": [item.to_dict() for item in self.signs],
            "overall_score": self.overall_score,
            "overall_classification": self.overall_classification,
            "available_count": self.available_count,
            "unavailable_count": self.unavailable_count,
            "formula_set_version": self.formula_set_version,
        }
