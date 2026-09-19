from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_code: str
    created_at: datetime
    source_observation_ids: tuple[str, ...]
    measured_values: dict[str, Any]
    comparison_basis: dict[str, Any]
    rule_version: str
    low_sample: bool
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_code": self.evidence_code,
            "created_at": self.created_at.isoformat(),
            "source_observation_ids": list(self.source_observation_ids),
            "measured_values": self.measured_values,
            "comparison_basis": self.comparison_basis,
            "rule_version": self.rule_version,
            "low_sample": self.low_sample,
            "fingerprint": self.fingerprint,
        }
