from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class FindingRecord:
    finding_id: str
    finding_code: str
    severity: str
    confidence: int
    created_at: datetime
    evidence_ids: tuple[str, ...]
    vital_profile_id: str
    vital_sign_code: str | None
    affected_period: dict[str, str]
    rule_version: str
    rationale: dict[str, Any]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_code": self.finding_code,
            "severity": self.severity,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "evidence_ids": list(self.evidence_ids),
            "vital_profile_id": self.vital_profile_id,
            "vital_sign_code": self.vital_sign_code,
            "affected_period": self.affected_period,
            "rule_version": self.rule_version,
            "rationale": self.rationale,
            "fingerprint": self.fingerprint,
        }
