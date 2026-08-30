from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceFactors:
    evidence_score: int = 100
    low_sample: bool = False
    missing_serp: bool = False
    missing_cross_article: bool = False
    conflicting_signals: bool = False
    data_quality_warning: bool = False
    verified_official_source: bool = False


def calculate_confidence(factors: ConfidenceFactors) -> int:
    score = max(0, min(100, factors.evidence_score))
    score -= 20 if factors.low_sample else 0
    score -= 10 if factors.missing_serp else 0
    score -= 10 if factors.missing_cross_article else 0
    score -= 10 if factors.conflicting_signals else 0
    score -= 10 if factors.data_quality_warning else 0
    score += 5 if factors.verified_official_source else 0
    return max(0, min(100, score))
