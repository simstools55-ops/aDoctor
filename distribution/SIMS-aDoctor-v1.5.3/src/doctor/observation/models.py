from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ObservationEvent:
    observation_id: str
    observation_type: str
    observed_at: datetime
    source: str
    facts: dict[str, Any]
    schema_version: str = "1.0"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_code: str
    created_at: datetime
    source_observation_ids: tuple[str, ...]
    measured_values: dict[str, Any]
    comparison_basis: dict[str, Any]
    rule_version: str
    low_sample: bool = False


@dataclass(frozen=True)
class VitalSign:
    code: str
    score: int
    classification: str
    calculated_at: datetime
    evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    formula_version: str = "UNIMPLEMENTED"


@dataclass(frozen=True)
class Finding:
    finding_id: str
    code: str
    severity: str
    confidence: int
    created_at: datetime
    evidence_ids: tuple[str, ...]
    affected_period: dict[str, str]
    rule_version: str

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 100:
            raise ValueError("Finding confidence must be from 0 to 100")
