from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExternalFactorType(str, Enum):
    OFFICIAL_EVENT = "OFFICIAL_EVENT"
    PROGRAM_CHANGE = "PROGRAM_CHANGE"
    SERVICE_END = "SERVICE_END"
    SEASONALITY = "SEASONALITY"
    MARKET_CONTRACTION = "MARKET_CONTRACTION"


class DemandHealth(str, Enum):
    GROWING = "GROWING"
    STABLE = "STABLE"
    SHRINKING = "SHRINKING"
    COLLAPSED = "COLLAPSED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ExternalFactor:
    factor_type: ExternalFactorType
    demand_health: DemandHealth
    confidence: int
    source_type: str
    source_label: str
    observed_at: str
    summary_ja: str

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")

    def excludes_improvement_failure(self) -> bool:
        return self.confidence >= 80 and self.demand_health in {
            DemandHealth.SHRINKING,
            DemandHealth.COLLAPSED,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.factor_type.value,
            "demand_health": self.demand_health.value,
            "confidence": self.confidence,
            "source_type": self.source_type,
            "source_label": self.source_label,
            "observed_at": self.observed_at,
            "summary_ja": self.summary_ja,
            "excludes_improvement_failure": self.excludes_improvement_failure(),
        }
