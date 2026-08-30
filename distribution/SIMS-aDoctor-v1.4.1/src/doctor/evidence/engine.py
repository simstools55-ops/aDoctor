from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from .models import EvidenceRecord


class EvidenceEngineError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(code: str, observation_ids: tuple[str, ...], measured_values: dict[str, Any], rule_version: str) -> str:
    raw = {
        "code": code,
        "observation_ids": sorted(observation_ids),
        "measured_values": measured_values,
        "rule_version": rule_version,
    }
    return hashlib.sha256(_canonical(raw).encode("utf-8")).hexdigest()


def _evidence_id(now: datetime) -> str:
    return f"EVD-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class EvidenceEngine:
    def __init__(self, ckb: ClinicalKnowledgeBase, event_log: MedicalRecordEventLog) -> None:
        self.ckb = ckb
        self.event_log = event_log
        self.rules = ckb.evidence_rules()
        self.sample_policy = ckb.sample_policy()

    def extract_all(self, medical_record: dict[str, Any]) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        search_observations = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") == "SEARCH_CONSOLE"
        ]
        metadata_observations = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") == "METADATA"
        ]

        if search_observations:
            current = search_observations[-1]
            for builder in (
                self._ctr_below_expectation,
                self._position_decline,
                self._visibility_decline,
            ):
                result = builder(current)
                if result:
                    saved = self._save(medical_record, result)
                    if saved is not None:
                        created.append(saved)

        if metadata_observations:
            result = self._long_time_since_update(metadata_observations[-1])
            if result:
                saved = self._save(medical_record, result)
                if saved is not None:
                    created.append(saved)

        return created

    def _ctr_below_expectation(self, observation: dict[str, Any]) -> EvidenceRecord | None:
        period = observation["facts"]["periods"]["days_28"]
        position = period.get("position")
        if position is None:
            return None
        rule = self.rules["CTR_BELOW_POSITION_EXPECTATION"]
        expected = None
        for band in rule["parameters"]["position_bands"]:
            if band["min_position"] <= position <= band["max_position"]:
                expected = band["minimum_expected_ctr"]
                break
        if expected is None or period["ctr"] >= expected:
            return None
        low_sample = (
            period["impressions"] < self.sample_policy["minimum_impressions_for_ctr"]
            or period["clicks"] < self.sample_policy["minimum_clicks_for_ctr_support"]
        )
        return self._record(
            code="CTR_BELOW_POSITION_EXPECTATION",
            observation_ids=(observation["observation_id"],),
            measured_values={
                "ctr": period["ctr"],
                "position": position,
                "impressions": period["impressions"],
                "clicks": period["clicks"],
            },
            comparison_basis={"minimum_expected_ctr": expected, "period": "days_28"},
            rule_version=rule["rule_version"],
            low_sample=low_sample,
        )

    def _position_decline(self, observation: dict[str, Any]) -> EvidenceRecord | None:
        periods = observation["facts"]["periods"]
        current = periods["days_28"]
        baseline = periods["days_90"]
        if current["position"] is None or baseline["position"] is None:
            return None
        absolute = current["position"] - baseline["position"]
        relative = absolute / baseline["position"] if baseline["position"] else 0.0
        rule = self.rules["POSITION_DECLINE_OBSERVED"]
        params = rule["parameters"]
        if absolute < params["minimum_absolute_decline"] or relative < params["minimum_relative_decline_ratio"]:
            return None
        low_sample = min(current["impressions"], baseline["impressions"]) < self.sample_policy["minimum_impressions_for_trend"]
        return self._record(
            code="POSITION_DECLINE_OBSERVED",
            observation_ids=(observation["observation_id"],),
            measured_values={
                "current_position": current["position"],
                "baseline_position": baseline["position"],
                "absolute_decline": absolute,
                "relative_decline_ratio": relative,
            },
            comparison_basis={"current_period": "days_28", "baseline_period": "days_90"},
            rule_version=rule["rule_version"],
            low_sample=low_sample,
        )

    def _visibility_decline(self, observation: dict[str, Any]) -> EvidenceRecord | None:
        periods = observation["facts"]["periods"]
        current = periods["days_28"]
        baseline = periods["days_90"]
        # Normalize 90-day aggregate to a 28-day expected value.
        baseline_28 = baseline["impressions"] * (28 / 90)
        if baseline_28 <= 0:
            return None
        decline_ratio = (baseline_28 - current["impressions"]) / baseline_28
        rule = self.rules["VISIBILITY_DECLINE_OBSERVED"]
        if decline_ratio < rule["parameters"]["minimum_decline_ratio"]:
            return None
        low_sample = min(current["impressions"], baseline_28) < self.sample_policy["minimum_impressions_for_trend"]
        return self._record(
            code="VISIBILITY_DECLINE_OBSERVED",
            observation_ids=(observation["observation_id"],),
            measured_values={
                "current_impressions": current["impressions"],
                "baseline_28_day_equivalent": baseline_28,
                "decline_ratio": decline_ratio,
            },
            comparison_basis={"current_period": "days_28", "baseline_period": "days_90_normalized"},
            rule_version=rule["rule_version"],
            low_sample=low_sample,
        )

    def _long_time_since_update(self, observation: dict[str, Any]) -> EvidenceRecord | None:
        facts = observation.get("facts", {})
        last_modified = facts.get("last_modified_at")
        observed_at = observation.get("observed_at")
        if not last_modified or not observed_at:
            return None
        modified_dt = datetime.fromisoformat(last_modified)
        observed_dt = datetime.fromisoformat(observed_at)
        days = (observed_dt.date() - modified_dt.date()).days
        rule = self.rules["LONG_TIME_SINCE_UPDATE"]
        minimum = rule["parameters"]["minimum_days_since_update"]
        if days < minimum:
            return None
        return self._record(
            code="LONG_TIME_SINCE_UPDATE",
            observation_ids=(observation["observation_id"],),
            measured_values={"days_since_update": days, "last_modified_at": last_modified},
            comparison_basis={"minimum_days_since_update": minimum},
            rule_version=rule["rule_version"],
            low_sample=False,
        )

    def _record(
        self,
        *,
        code: str,
        observation_ids: tuple[str, ...],
        measured_values: dict[str, Any],
        comparison_basis: dict[str, Any],
        rule_version: str,
        low_sample: bool,
    ) -> EvidenceRecord:
        if not self.ckb.is_known_code("evidence", code):
            raise EvidenceEngineError(f"Unknown evidence code: {code}")
        now = datetime.now(timezone.utc)
        fingerprint = _fingerprint(code, observation_ids, measured_values, rule_version)
        return EvidenceRecord(
            evidence_id=_evidence_id(now),
            evidence_code=code,
            created_at=now,
            source_observation_ids=observation_ids,
            measured_values=measured_values,
            comparison_basis=comparison_basis,
            rule_version=rule_version,
            low_sample=low_sample,
            fingerprint=fingerprint,
        )

    def _save(self, medical_record: dict[str, Any], evidence: EvidenceRecord) -> dict[str, Any] | None:
        existing = medical_record.setdefault("evidence", [])
        for item in existing:
            if item.get("fingerprint") == evidence.fingerprint:
                return None

        data = evidence.to_dict()
        self.event_log.append(
            medical_record,
            event_type="EVIDENCE_RECORDED",
            payload={"evidence": data},
            occurred_at=evidence.created_at,
            idempotency_key=f"evidence:{evidence.fingerprint}",
        )
        existing.append(data)
        counters = medical_record.setdefault("counters", {})
        counters["evidence_count"] = len(existing)
        medical_record["updated_at"] = evidence.created_at.isoformat()
        return data
