from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from .models import FindingRecord


class FindingsEngineError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _finding_id(now: datetime) -> str:
    return f"FND-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


def _fingerprint(code: str, evidence_ids: tuple[str, ...], profile_id: str, severity: str, rule_version: str) -> str:
    raw = {
        "code": code,
        "evidence_ids": sorted(evidence_ids),
        "profile_id": profile_id,
        "severity": severity,
        "rule_version": rule_version,
    }
    return hashlib.sha256(_canonical(raw).encode("utf-8")).hexdigest()


class FindingsEngine:
    def __init__(self, ckb: ClinicalKnowledgeBase, event_log: MedicalRecordEventLog) -> None:
        self.ckb = ckb
        self.event_log = event_log
        self.rules = ckb.finding_rules()
        self.policy = ckb.finding_global_policy()

    def generate_all(self, medical_record: dict[str, Any]) -> list[dict[str, Any]]:
        profiles = medical_record.get("vital_profiles", [])
        if not profiles:
            return []
        profile = profiles[-1]
        signs = {item["code"]: item for item in profile["signs"]}
        evidence = medical_record.get("evidence", [])
        evidence_by_code: dict[str, list[dict[str, Any]]] = {}
        for item in evidence:
            evidence_by_code.setdefault(item["evidence_code"], []).append(item)

        created: list[dict[str, Any]] = []
        for code, rule in self.rules.items():
            if code == "INSUFFICIENT_EVIDENCE":
                continue
            item = self._build_from_rule(rule, profile, signs, evidence_by_code)
            if item is not None:
                saved = self._save(medical_record, item)
                if saved is not None:
                    created.append(saved)

        low_sample_only = bool(evidence) and all(item.get("low_sample") for item in evidence)
        if low_sample_only:
            item = self._build_insufficient_evidence(profile, evidence)
            saved = self._save(medical_record, item)
            if saved is not None:
                created.append(saved)

        return created

    def _build_from_rule(
        self,
        rule: dict[str, Any],
        profile: dict[str, Any],
        signs: dict[str, dict[str, Any]],
        evidence_by_code: dict[str, list[dict[str, Any]]],
    ) -> FindingRecord | None:
        required_codes = tuple(rule.get("required_evidence", []))
        related: list[dict[str, Any]] = []
        for code in required_codes:
            items = evidence_by_code.get(code)
            if not items:
                return None
            related.extend(items)

        vital_code = rule.get("required_vital_sign")
        vital = signs.get(vital_code) if vital_code else None
        if vital_code and (vital is None or vital.get("status") != "AVAILABLE" or vital.get("score") is None):
            return None

        additional = rule.get("additional_conditions", {})
        if "visibility_min_score" in additional:
            visibility = signs.get("VISIBILITY")
            if not visibility or visibility.get("score") is None:
                return None
            if visibility["score"] < additional["visibility_min_score"]:
                return None

        score = vital["score"] if vital else None
        severity = self._severity(rule, score)
        if severity is None:
            return None

        low_sample = any(item.get("low_sample") for item in related)
        confidence = rule["base_confidence"]
        if low_sample:
            confidence -= self.policy["low_sample_confidence_penalty"]
        confidence = max(0, min(100, confidence))

        now = datetime.now(timezone.utc)
        evidence_ids = tuple(item["evidence_id"] for item in related)
        affected_period = self._affected_period(related)
        fp = _fingerprint(
            rule["finding_code"], evidence_ids, profile["profile_id"],
            severity, rule["rule_version"]
        )
        return FindingRecord(
            finding_id=_finding_id(now),
            finding_code=rule["finding_code"],
            severity=severity,
            confidence=confidence,
            created_at=now,
            evidence_ids=evidence_ids,
            vital_profile_id=profile["profile_id"],
            vital_sign_code=vital_code,
            affected_period=affected_period,
            rule_version=rule["rule_version"],
            rationale={
                "vital_score": score,
                "vital_classification": vital.get("classification") if vital else None,
                "low_sample": low_sample,
                "required_evidence_codes": list(required_codes),
            },
            fingerprint=fp,
        )

    def _build_insufficient_evidence(
        self, profile: dict[str, Any], evidence: list[dict[str, Any]]
    ) -> FindingRecord:
        rule = self.rules["INSUFFICIENT_EVIDENCE"]
        now = datetime.now(timezone.utc)
        evidence_ids = tuple(item["evidence_id"] for item in evidence)
        fp = _fingerprint(
            "INSUFFICIENT_EVIDENCE", evidence_ids, profile["profile_id"],
            rule["severity"], rule["rule_version"]
        )
        return FindingRecord(
            finding_id=_finding_id(now),
            finding_code="INSUFFICIENT_EVIDENCE",
            severity=rule["severity"],
            confidence=rule["base_confidence"],
            created_at=now,
            evidence_ids=evidence_ids,
            vital_profile_id=profile["profile_id"],
            vital_sign_code=None,
            affected_period=self._affected_period(evidence),
            rule_version=rule["rule_version"],
            rationale={"reason": "All available Evidence items are LOW_SAMPLE"},
            fingerprint=fp,
        )

    @staticmethod
    def _severity(rule: dict[str, Any], score: int | None) -> str | None:
        if "severity" in rule:
            return rule["severity"]
        if score is None:
            return None
        for band in rule.get("severity_by_score", []):
            if band["min"] <= score <= band["max"]:
                return band["severity"]
        return None

    @staticmethod
    def _affected_period(evidence: list[dict[str, Any]]) -> dict[str, str]:
        periods = []
        for item in evidence:
            basis = item.get("comparison_basis", {})
            for key in ("current_period", "baseline_period", "period"):
                value = basis.get(key)
                if value:
                    periods.append(str(value))
        return {
            "start": min(periods) if periods else "UNKNOWN",
            "end": max(periods) if periods else "UNKNOWN",
        }

    def _save(self, medical_record: dict[str, Any], finding: FindingRecord) -> dict[str, Any] | None:
        stored = medical_record.setdefault("findings", [])
        for item in stored:
            if item.get("fingerprint") == finding.fingerprint:
                return None

        data = finding.to_dict()
        self.event_log.append(
            medical_record,
            event_type="FINDING_RECORDED",
            payload={"finding": data},
            occurred_at=finding.created_at,
            idempotency_key=f"finding:{finding.fingerprint}",
        )
        stored.append(data)
        counters = medical_record.setdefault("counters", {})
        counters["finding_count"] = len(stored)
        medical_record["updated_at"] = finding.created_at.isoformat()
        return data
