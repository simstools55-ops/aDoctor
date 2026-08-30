from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DifferentialCandidate:
    diagnosis_code: str
    rank: int
    confidence: int
    priority: int
    supporting_finding_ids: tuple[str, ...]
    contradicting_finding_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    rule_version: str
    rationale: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnosis_code": self.diagnosis_code,
            "rank": self.rank,
            "confidence": self.confidence,
            "priority": self.priority,
            "supporting_finding_ids": list(self.supporting_finding_ids),
            "contradicting_finding_ids": list(self.contradicting_finding_ids),
            "evidence_ids": list(self.evidence_ids),
            "rule_version": self.rule_version,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class DifferentialAssessment:
    differential_id: str
    created_at: datetime
    candidates: tuple[DifferentialCandidate, ...]
    finding_ids: tuple[str, ...]
    top_candidate: str | None
    top_confidence: int | None
    rule_set_version: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "differential_id": self.differential_id,
            "created_at": self.created_at.isoformat(),
            "candidates": [item.to_dict() for item in self.candidates],
            "finding_ids": list(self.finding_ids),
            "top_candidate": self.top_candidate,
            "top_confidence": self.top_confidence,
            "rule_set_version": self.rule_set_version,
            "fingerprint": self.fingerprint,
        }
