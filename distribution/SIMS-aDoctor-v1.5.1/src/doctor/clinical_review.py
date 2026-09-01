from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class ClinicalFindingCode(str, Enum):
    INTERNAL_CONTRADICTION = "INTERNAL_CONTRADICTION"
    FACTUAL_CORRECTION_REQUIRED = "FACTUAL_CORRECTION_REQUIRED"
    FRESHNESS_VERIFICATION_REQUIRED = "FRESHNESS_VERIFICATION_REQUIRED"
    LOW_RELEVANCE_INTERNAL_LINKS = "LOW_RELEVANCE_INTERNAL_LINKS"
    TITLE_BODY_MISMATCH = "TITLE_BODY_MISMATCH"


class ClinicalAction(str, Enum):
    NONE = "NONE"
    LIMITED_CONTENT_REPAIR = "LIMITED_CONTENT_REPAIR"
    FACT_CHECK = "FACT_CHECK"
    MONITOR = "MONITOR"


@dataclass(frozen=True)
class ClinicalFinding:
    code: ClinicalFindingCode
    summary_ja: str
    evidence: tuple[str, ...] = ()
    confidence: int = 0
    requires_immediate_correction: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "summary_ja": self.summary_ja,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "requires_immediate_correction": self.requires_immediate_correction,
        }


@dataclass(frozen=True)
class ClinicalReviewResult:
    status: str
    action: ClinicalAction
    findings: tuple[ClinicalFinding, ...] = field(default_factory=tuple)
    low_sample_override_applied: bool = False

    @property
    def correction_required(self) -> bool:
        return any(f.requires_immediate_correction for f in self.findings)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action.value,
            "findings": [f.to_dict() for f in self.findings],
            "low_sample_override_applied": self.low_sample_override_applied,
            "correction_required": self.correction_required,
        }


def apply_low_sample_safety(
    *, low_sample: bool, findings: Iterable[ClinicalFinding]
) -> ClinicalReviewResult:
    """Protect SEO performance decisions without suppressing factual repairs.

    LOW_SAMPLE blocks broad SEO rewrites, but never blocks an explicit factual
    correction, internal contradiction repair, or freshness verification.
    """
    normalized = tuple(findings)
    urgent = any(f.requires_immediate_correction for f in normalized)
    if urgent:
        return ClinicalReviewResult(
            status="CORRECTION_REQUIRED",
            action=ClinicalAction.LIMITED_CONTENT_REPAIR,
            findings=normalized,
            low_sample_override_applied=low_sample,
        )
    return ClinicalReviewResult(
        status="MONITOR" if low_sample else "NO_ISSUE_CONFIRMED",
        action=ClinicalAction.MONITOR if low_sample else ClinicalAction.NONE,
        findings=normalized,
        low_sample_override_applied=False,
    )
