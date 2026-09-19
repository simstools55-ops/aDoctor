from __future__ import annotations

from datetime import datetime, timezone
import math
import secrets
from statistics import mean
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from .models import VitalProfile, VitalSignResult


class VitalSignsEngineError(ValueError):
    pass


def _clamp(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _profile_id(now: datetime) -> str:
    return f"VPR-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class VitalSignsEngine:
    def __init__(self, ckb: ClinicalKnowledgeBase, event_log: MedicalRecordEventLog) -> None:
        self.ckb = ckb
        self.event_log = event_log
        self.formulas = ckb.vital_formulas()
        self.policy = ckb.vital_global_policy()

    def calculate(self, medical_record: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        existing = self._find_existing(medical_record, idempotency_key)
        if existing is not None:
            return existing

        observations = medical_record.get("observations", [])
        evidence = medical_record.get("evidence", [])
        search = self._latest_observation(observations, "SEARCH_CONSOLE")
        metadata = self._latest_observation(observations, "METADATA")
        now = datetime.now(timezone.utc)

        source_observation_ids = tuple(
            item["observation_id"] for item in (search, metadata) if item is not None
        )
        evidence_ids = tuple(item["evidence_id"] for item in evidence)

        signs = (
            self._visibility(search, evidence, now),
            self._traffic(search, evidence, now),
            self._ctr_health(search, evidence, now),
            self._ranking_stability(search, evidence, now),
            self._freshness(metadata, evidence, now),
            self._competition_resilience(self._latest_observation(observations, "SERP"), evidence, now),
            self._content_integrity(self._latest_observation(observations, "ARTICLE_SNAPSHOT"), self._latest_observation(observations, "SERP"), evidence, now),
        )

        available_scores = [item.score for item in signs if item.score is not None]
        overall_score = _clamp(mean(available_scores)) if available_scores else None
        overall_classification = (
            self.ckb.classify_vital_score(overall_score)
            if overall_score is not None else None
        )

        profile = VitalProfile(
            profile_id=_profile_id(now),
            calculated_at=now,
            source_observation_ids=source_observation_ids,
            evidence_ids=evidence_ids,
            signs=signs,
            overall_score=overall_score,
            overall_classification=overall_classification,
            available_count=len(available_scores),
            unavailable_count=len(signs) - len(available_scores),
            formula_set_version="1.0",
        )
        data = profile.to_dict()

        self.event_log.append(
            medical_record,
            event_type="VITAL_SIGNS_CALCULATED",
            payload={"vital_profile": data},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("vital_profiles", []).append(data)
        counters = medical_record.setdefault("counters", {})
        counters["vital_profile_count"] = len(medical_record["vital_profiles"])
        medical_record["updated_at"] = now.isoformat()
        return data

    @staticmethod
    def _latest_observation(observations: list[dict[str, Any]], observation_type: str) -> dict[str, Any] | None:
        matches = [item for item in observations if item.get("observation_type") == observation_type]
        return matches[-1] if matches else None

    @staticmethod
    def _find_existing(medical_record: dict[str, Any], idempotency_key: str) -> dict[str, Any] | None:
        for event in medical_record.get("events", []):
            if event.get("event_type") == "VITAL_SIGNS_CALCULATED" and event.get("idempotency_key") == idempotency_key:
                return event["payload"]["vital_profile"]
        return None

    def _result(
        self,
        code: str,
        score: float,
        now: datetime,
        *,
        observation_ids: tuple[str, ...],
        evidence_items: list[dict[str, Any]],
        details: dict[str, Any],
        base_confidence: int = 85,
    ) -> VitalSignResult:
        low_sample = any(item.get("low_sample") for item in evidence_items)
        final_score = _clamp(score - (self.policy["low_sample_penalty"] if low_sample else 0))
        confidence = max(0, base_confidence - (25 if low_sample else 0))
        return VitalSignResult(
            code=code,
            status="AVAILABLE",
            score=final_score,
            classification=self.ckb.classify_vital_score(final_score),
            confidence=confidence,
            calculated_at=now,
            evidence_ids=tuple(item["evidence_id"] for item in evidence_items),
            source_observation_ids=observation_ids,
            formula_version=self.formulas[code]["version"],
            details={**details, "low_sample_penalty_applied": low_sample},
        )

    def _unavailable(self, code: str, now: datetime, reason: str) -> VitalSignResult:
        return VitalSignResult(
            code=code,
            status="UNAVAILABLE",
            score=None,
            classification=None,
            confidence=0,
            calculated_at=now,
            evidence_ids=(),
            source_observation_ids=(),
            formula_version=self.formulas[code]["version"],
            details={"reason": reason},
        )

    def _visibility(self, search: dict[str, Any] | None, evidence: list[dict[str, Any]], now: datetime) -> VitalSignResult:
        if search is None:
            return self._unavailable("VISIBILITY", now, "Search Console observation is not available")
        p = search["facts"]["periods"]
        current = p["days_28"]["impressions"]
        baseline = p["days_90"]["impressions"] * (28 / 90)
        historical = p["days_365"]["impressions"] * (28 / 365)
        current_level = 100 if current >= max(baseline, historical, 1) else 100 * current / max(baseline, historical, 1)
        trend = 100 if current >= baseline else 100 * current / max(baseline, 1)
        presence = min(100, 100 * current / max(historical, 1))
        score = current_level * 0.4 + trend * 0.4 + presence * 0.2
        related = [x for x in evidence if x["evidence_code"] == "VISIBILITY_DECLINE_OBSERVED"]
        return self._result(
            "VISIBILITY", score, now,
            observation_ids=(search["observation_id"],),
            evidence_items=related,
            details={"current_impressions": current, "baseline_28_equivalent": baseline}
        )

    def _traffic(self, search: dict[str, Any] | None, evidence: list[dict[str, Any]], now: datetime) -> VitalSignResult:
        if search is None:
            return self._unavailable("TRAFFIC", now, "Search Console observation is not available")
        p = search["facts"]["periods"]
        current = p["days_28"]["clicks"]
        baseline = p["days_90"]["clicks"] * (28 / 90)
        historical = p["days_365"]["clicks"] * (28 / 365)
        current_level = min(100, 100 * current / max(historical, 1))
        trend = 100 if current >= baseline else 100 * current / max(baseline, 1)
        score = current_level * 0.5 + trend * 0.5
        return self._result(
            "TRAFFIC", score, now,
            observation_ids=(search["observation_id"],),
            evidence_items=[],
            details={"current_clicks": current, "baseline_28_equivalent": baseline}
        )

    def _ctr_health(self, search: dict[str, Any] | None, evidence: list[dict[str, Any]], now: datetime) -> VitalSignResult:
        if search is None:
            return self._unavailable("CTR_HEALTH", now, "Search Console observation is not available")
        period = search["facts"]["periods"]["days_28"]
        position = period["position"]
        if position is None:
            return self._unavailable("CTR_HEALTH", now, "Current position is unavailable")
        expected = 0.08 if position <= 3 else 0.04 if position <= 5 else 0.015 if position <= 10 else 0.005
        ratio = min(1.0, period["ctr"] / expected) if expected else 0
        related = [x for x in evidence if x["evidence_code"] == "CTR_BELOW_POSITION_EXPECTATION"]
        score = ratio * 100
        if related:
            score *= 0.8
        return self._result(
            "CTR_HEALTH", score, now,
            observation_ids=(search["observation_id"],),
            evidence_items=related,
            details={"ctr": period["ctr"], "position": position, "expected_ctr": expected}
        )

    def _ranking_stability(self, search: dict[str, Any] | None, evidence: list[dict[str, Any]], now: datetime) -> VitalSignResult:
        if search is None:
            return self._unavailable("RANKING_STABILITY", now, "Search Console observation is not available")
        p = search["facts"]["periods"]
        positions = [p[key]["position"] for key in ("days_28", "days_90", "days_365")]
        if any(value is None for value in positions):
            return self._unavailable("RANKING_STABILITY", now, "One or more position values are unavailable")
        spread = max(positions) - min(positions)
        score = max(0, 100 - spread * 12)
        related = [x for x in evidence if x["evidence_code"] == "POSITION_DECLINE_OBSERVED"]
        if related:
            score *= 0.7
        return self._result(
            "RANKING_STABILITY", score, now,
            observation_ids=(search["observation_id"],),
            evidence_items=related,
            details={"positions": positions, "spread": spread}
        )



    def _competition_resilience(self, serp: dict[str, Any] | None, evidence: list[dict[str, Any]], now: datetime) -> VitalSignResult:
        if serp is None:
            return self._unavailable("COMPETITION_RESILIENCE", now, "SERP observation is not available")
        competition = serp.get("facts", {}).get("competition", {})
        strength = competition.get("strength_score")
        intent_match = competition.get("intent_match_score")
        if strength is None or intent_match is None:
            return self._unavailable("COMPETITION_RESILIENCE", now, "SERP competition metrics are unavailable")
        score = 100 - strength * 0.7 + intent_match * 0.3
        return self._result(
            "COMPETITION_RESILIENCE", score, now,
            observation_ids=(serp["observation_id"],),
            evidence_items=[],
            details={
                "competition_strength": strength,
                "serp_intent_match": intent_match,
            },
            base_confidence=75,
        )



    def _content_integrity(
        self,
        article: dict[str, Any] | None,
        serp: dict[str, Any] | None,
        evidence: list[dict[str, Any]],
        now: datetime,
    ) -> VitalSignResult:
        if article is None:
            return self._unavailable("CONTENT_INTEGRITY", now, "Article Snapshot observation is not available")
        facts = article.get("facts", {})
        metrics = facts.get("metrics", {})
        title_score = 100 if facts.get("title") else 0
        heading_score = min(100, metrics.get("heading_count", 0) / 3 * 100)
        faq_score = min(100, metrics.get("faq_count", 0) * 100)
        link_score = min(100, metrics.get("internal_link_count", 0) / 2 * 100)
        intent_score = facts.get("intent_alignment", {}).get("score", 0)
        freshness_score = 100 if facts.get("freshness_markers") else 50

        weights = {
            "title": 0.10,
            "heading": 0.20,
            "faq": 0.15,
            "links": 0.15,
            "intent": 0.25,
            "freshness": 0.15,
        }
        score = (
            title_score * weights["title"]
            + heading_score * weights["heading"]
            + faq_score * weights["faq"]
            + link_score * weights["links"]
            + intent_score * weights["intent"]
            + freshness_score * weights["freshness"]
        )

        observation_ids = [article["observation_id"]]
        if serp is not None:
            observation_ids.append(serp["observation_id"])

        return self._result(
            "CONTENT_INTEGRITY", score, now,
            observation_ids=tuple(observation_ids),
            evidence_items=[],
            details={
                "title_score": title_score,
                "heading_score": round(heading_score),
                "faq_score": round(faq_score),
                "internal_link_score": round(link_score),
                "intent_alignment_score": intent_score,
                "freshness_marker_score": freshness_score,
            },
            base_confidence=80 if serp is not None else 70,
        )

    def _freshness(self, metadata: dict[str, Any] | None, evidence: list[dict[str, Any]], now: datetime) -> VitalSignResult:
        if metadata is None:
            return self._unavailable("FRESHNESS", now, "Metadata observation is not available")
        last_modified = metadata.get("facts", {}).get("last_modified_at")
        if not last_modified:
            return self._unavailable("FRESHNESS", now, "last_modified_at is unavailable")
        modified = datetime.fromisoformat(last_modified)
        days = (now.date() - modified.date()).days
        params = self.formulas["FRESHNESS"]["parameters"]
        full_days = params["full_score_days"]
        zero_days = params["zero_score_days"]
        if days <= full_days:
            score = 100
        elif days >= zero_days:
            score = 0
        else:
            score = 100 * (1 - (days - full_days) / (zero_days - full_days))
        related = [x for x in evidence if x["evidence_code"] == "LONG_TIME_SINCE_UPDATE"]
        return self._result(
            "FRESHNESS", score, now,
            observation_ids=(metadata["observation_id"],),
            evidence_items=related,
            details={"days_since_update": days, "last_modified_at": last_modified}
        )
