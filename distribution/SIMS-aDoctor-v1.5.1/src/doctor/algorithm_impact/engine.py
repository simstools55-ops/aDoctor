from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from .models import AlgorithmImpactAssessment


_LEVEL_VALUE = {"NONE": 0.0, "LOW": 0.25, "MEDIUM": 0.5, "HIGH": 1.0, "UNKNOWN": 0.0}


def _assessment_id(now: datetime) -> str:
    return f"AIA-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


def _level(value: Any) -> str:
    if value is True:
        return "HIGH"
    if value is False or value is None:
        return "NONE" if value is False else "UNKNOWN"
    text = str(value).upper()
    aliases = {
        "LIKELY": "HIGH",
        "POSSIBLE": "MEDIUM",
        "MODERATE": "MEDIUM",
        "YES": "HIGH",
        "NO": "NONE",
    }
    text = aliases.get(text, text)
    return text if text in _LEVEL_VALUE else "UNKNOWN"


class AlgorithmImpactEngine:
    """Evaluate algorithm-update impact as evidence, never as diagnosis.

    Expected input is ``medical_record['algorithm_context']``. The context may
    be assembled by a web-enabled Doctor adapter and/or SBM. This engine stays
    deterministic and does not fetch the web itself.
    """

    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def assess(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        context = medical_record.get("algorithm_context") or {}
        now = datetime.now(timezone.utc)
        update = dict(context.get("update") or {})
        source_status = str(update.get("source_status") or "UNKNOWN").upper()
        detected = update.get("detected")

        if not context:
            return self._unknown(now, "ALGORITHM_EVIDENCE_NOT_PROVIDED")
        if detected is False and source_status == "OFFICIAL_NOT_FOUND":
            return self._none(now, update, "NO_OFFICIAL_UPDATE_OVERLAP")
        if detected is not True:
            return self._unknown(now, "OFFICIAL_UPDATE_STATUS_UNKNOWN", update=update)

        signals = context.get("correlation") or {}
        correlation = {
            "temporal": _level(signals.get("temporal")),
            "site_wide": _level(signals.get("site_wide")),
            "segment": _level(signals.get("segment")),
            "article": _level(signals.get("article")),
            "serp": _level(signals.get("serp")),
        }
        weights = self.policy["weights"]
        score = round(sum(_LEVEL_VALUE[correlation[key]] * weights[key] for key in weights))
        score = max(0, min(100, score))

        thresholds = self.policy["thresholds"]
        if score >= thresholds["high"]:
            status = "HIGH"
        elif score >= thresholds["likely"]:
            status = "LIKELY"
        elif score >= thresholds["possible"]:
            status = "POSSIBLE"
        elif score >= thresholds["low"]:
            status = "LOW"
        else:
            status = "NONE"

        confidence = self._confidence(context, correlation, source_status)
        role = self._role(status, correlation)
        reasons = ["ALGORITHM_UPDATE_OVERLAP"]
        if correlation["site_wide"] == "HIGH":
            reasons.append("SITE_WIDE_SHIFT_DURING_UPDATE")
        if correlation["segment"] == "HIGH":
            reasons.append("SEGMENT_WIDE_SHIFT_DURING_UPDATE")
        if correlation["serp"] in {"MEDIUM", "HIGH"}:
            reasons.append("SERP_SHIFT_DURING_UPDATE")
        if correlation["article"] == "HIGH" and correlation["site_wide"] in {"NONE", "LOW", "UNKNOWN"}:
            reasons.append("ARTICLE_ONLY_SHIFT_DURING_UPDATE")
        if status in {"NONE", "LOW"}:
            reasons.append("ALGORITHM_CAUSATION_INSUFFICIENT")
        if str(update.get("rollout_status") or "").upper() == "IN_PROGRESS":
            reasons.append("UPDATE_ROLLOUT_IN_PROGRESS")
        if str(update.get("rollout_status") or "").upper() == "COMPLETED":
            reasons.append("UPDATE_ROLLOUT_COMPLETED")

        evidence_confidence = self._evidence_confidence(context, confidence, source_status)
        result = AlgorithmImpactAssessment(
            assessment_id=_assessment_id(now),
            assessed_at=now,
            status=status,
            confidence=confidence,
            role=role,
            impact_score=score,
            update=update,
            correlation=correlation,
            evidence_confidence=evidence_confidence,
            reason_codes=tuple(dict.fromkeys(reasons)),
            evidence_refs=tuple(context.get("evidence_refs") or ()),
        )
        return result.to_dict()

    def _confidence(self, context: dict[str, Any], correlation: dict[str, str], source_status: str) -> str:
        supplied = context.get("evidence_confidence") or {}
        explicit = str(supplied.get("level") or "").upper()
        if explicit in {"LOW", "MEDIUM", "HIGH"}:
            return explicit
        known = sum(level != "UNKNOWN" for level in correlation.values())
        if source_status == "OFFICIAL_CONFIRMED" and known >= 4:
            return "HIGH"
        if source_status == "OFFICIAL_CONFIRMED" and known >= 2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _role(status: str, correlation: dict[str, str]) -> str:
        if status == "HIGH" and correlation["site_wide"] == "HIGH" and correlation["temporal"] == "HIGH":
            return "PRIMARY_FACTOR"
        if status in {"HIGH", "LIKELY"}:
            return "CONTRIBUTING_FACTOR"
        if status == "POSSIBLE":
            return "POSSIBLE_FACTOR"
        if status in {"LOW", "NONE"}:
            return "UNLIKELY_FACTOR"
        return "NOT_SUPPORTED"

    @staticmethod
    def _evidence_confidence(context: dict[str, Any], confidence: str, source_status: str) -> dict[str, Any]:
        supplied = dict(context.get("evidence_confidence") or {})
        return {
            "level": supplied.get("level") or confidence,
            "sample_quality": supplied.get("sample_quality") or "UNKNOWN",
            "freshness": supplied.get("freshness") or "CURRENT",
            "source_authority": supplied.get("source_authority") or ("PRIMARY" if source_status == "OFFICIAL_CONFIRMED" else "UNKNOWN"),
            "corroboration": supplied.get("corroboration") or "UNKNOWN",
        }

    def _unknown(self, now: datetime, reason: str, *, update: dict[str, Any] | None = None) -> dict[str, Any]:
        return AlgorithmImpactAssessment(
            assessment_id=_assessment_id(now), assessed_at=now, status="UNKNOWN", confidence="LOW",
            role="NOT_SUPPORTED", impact_score=0, update=update or {},
            correlation={key: "UNKNOWN" for key in self.policy["weights"]},
            evidence_confidence={"level": "LOW", "sample_quality": "UNKNOWN", "freshness": "UNKNOWN", "source_authority": "UNKNOWN", "corroboration": "NONE"},
            reason_codes=(reason,), evidence_refs=(),
        ).to_dict()

    def _none(self, now: datetime, update: dict[str, Any], reason: str) -> dict[str, Any]:
        return AlgorithmImpactAssessment(
            assessment_id=_assessment_id(now), assessed_at=now, status="NONE", confidence="HIGH",
            role="UNLIKELY_FACTOR", impact_score=0, update=update,
            correlation={key: "NONE" for key in self.policy["weights"]},
            evidence_confidence={"level": "HIGH", "sample_quality": "SUFFICIENT", "freshness": "CURRENT", "source_authority": "PRIMARY", "corroboration": "SINGLE_EVIDENCE"},
            reason_codes=(reason,), evidence_refs=(),
        ).to_dict()
