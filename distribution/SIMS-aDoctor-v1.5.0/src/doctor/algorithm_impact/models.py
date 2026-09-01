from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AlgorithmImpactAssessment:
    assessment_id: str
    assessed_at: datetime
    status: str
    confidence: str
    role: str
    impact_score: int
    update: dict[str, Any]
    correlation: dict[str, str]
    evidence_confidence: dict[str, Any]
    reason_codes: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_name": "SIMS_DOCTOR_ALGORITHM_IMPACT_ASSESSMENT_V1",
            "contract_version": "1.0",
            "assessment_id": self.assessment_id,
            "assessed_at": self.assessed_at.isoformat(),
            "status": self.status,
            "confidence": self.confidence,
            "role": self.role,
            "impact_score": self.impact_score,
            "update": self.update,
            "correlation": self.correlation,
            "evidence_confidence": self.evidence_confidence,
            "reason_codes": list(self.reason_codes),
            "evidence_refs": list(self.evidence_refs),
        }
