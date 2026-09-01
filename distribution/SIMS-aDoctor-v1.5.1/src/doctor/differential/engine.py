from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from .models import DifferentialAssessment, DifferentialCandidate


class DifferentialDiagnosisError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _differential_id(now: datetime) -> str:
    return f"DIF-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class DifferentialDiagnosisEngine:
    def __init__(self, ckb: ClinicalKnowledgeBase, event_log: MedicalRecordEventLog) -> None:
        self.ckb = ckb
        self.event_log = event_log
        self.rules = ckb.differential_rules()
        self.policy = ckb.differential_global_policy()

    def assess(self, medical_record: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        existing = self._find_existing(medical_record, idempotency_key)
        if existing is not None:
            return existing

        findings = medical_record.get("findings", [])
        by_code: dict[str, list[dict[str, Any]]] = {}
        for item in findings:
            by_code.setdefault(item["finding_code"], []).append(item)

        context = self._context(medical_record)
        provisional: list[dict[str, Any]] = []

        for diagnosis_code, rule in self.rules.items():
            candidate = self._evaluate(rule, by_code, context)
            if candidate is not None:
                provisional.append(candidate)

        provisional.sort(key=lambda x: (-x["confidence"], -x["priority"], x["diagnosis_code"]))
        provisional = provisional[: self.policy["candidate_limit"]]

        candidates = tuple(
            DifferentialCandidate(
                diagnosis_code=item["diagnosis_code"],
                rank=index,
                confidence=item["confidence"],
                priority=item["priority"],
                supporting_finding_ids=tuple(item["supporting_finding_ids"]),
                contradicting_finding_ids=tuple(item["contradicting_finding_ids"]),
                evidence_ids=tuple(item["evidence_ids"]),
                rule_version=item["rule_version"],
                rationale=item["rationale"],
            )
            for index, item in enumerate(provisional, start=1)
        )

        now = datetime.now(timezone.utc)
        fingerprint_source = {
            "finding_ids": sorted(item["finding_id"] for item in findings),
            "candidates": [
                {"code": item.diagnosis_code, "confidence": item.confidence}
                for item in candidates
            ],
            "rule_set_version": "1.0",
        }
        fingerprint = hashlib.sha256(_canonical(fingerprint_source).encode("utf-8")).hexdigest()

        assessment = DifferentialAssessment(
            differential_id=_differential_id(now),
            created_at=now,
            candidates=candidates,
            finding_ids=tuple(item["finding_id"] for item in findings),
            top_candidate=candidates[0].diagnosis_code if candidates else None,
            top_confidence=candidates[0].confidence if candidates else None,
            rule_set_version="1.0",
            fingerprint=fingerprint,
        )
        data = assessment.to_dict()

        self.event_log.append(
            medical_record,
            event_type="DIFFERENTIAL_UPDATED",
            payload={"differential": data},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("differential_assessments", []).append(data)
        counters = medical_record.setdefault("counters", {})
        counters["differential_count"] = len(medical_record["differential_assessments"])
        medical_record["case_status"] = "DIAGNOSING"
        medical_record["updated_at"] = now.isoformat()
        return data

    def _evaluate(
        self,
        rule: dict[str, Any],
        findings_by_code: dict[str, list[dict[str, Any]]],
        context: dict[str, bool],
    ) -> dict[str, Any] | None:
        required_context = rule.get("required_context", [])
        if any(not context.get(key, False) for key in required_context):
            return None

        supporting = []
        support_score = 0
        low_sample = False
        for item in rule.get("supporting_findings", []):
            matches = findings_by_code.get(item["code"], [])
            if matches:
                supporting.extend(matches)
                support_score += item["weight"]
                if any(match.get("rationale", {}).get("low_sample") for match in matches):
                    low_sample = True

        if len({item["finding_code"] for item in supporting}) < rule.get("minimum_support_count", 1):
            return None

        contradicting = []
        contradiction_score = 0
        for item in rule.get("contradicting_findings", []):
            matches = findings_by_code.get(item["code"], [])
            if matches:
                contradicting.extend(matches)
                contradiction_score += item["weight"]

        confidence = rule["base_confidence"] + support_score
        if low_sample:
            confidence -= self.policy["low_sample_penalty"]
        if contradicting:
            confidence -= max(self.policy["contradiction_penalty"], contradiction_score)

        confidence = max(0, min(100, confidence))
        if confidence < self.policy["minimum_candidate_confidence"]:
            return None

        evidence_ids = sorted({
            evidence_id
            for finding in supporting + contradicting
            for evidence_id in finding.get("evidence_ids", [])
        })

        return {
            "diagnosis_code": rule["diagnosis_code"],
            "confidence": confidence,
            "priority": rule["priority"],
            "supporting_finding_ids": [item["finding_id"] for item in supporting],
            "contradicting_finding_ids": [item["finding_id"] for item in contradicting],
            "evidence_ids": evidence_ids,
            "rule_version": rule.get("rule_version", "1.0"),
            "rationale": {
                "support_score": support_score,
                "contradiction_score": contradiction_score,
                "low_sample_penalty_applied": low_sample,
                "required_context": required_context,
            },
        }

    @staticmethod
    def _context(medical_record: dict[str, Any]) -> dict[str, bool]:
        history = medical_record.get("history", [])
        return {
            "history.improvement_event_exists": any(
                item.get("event_type") in {"IMPROVEMENT_RECORDED", "TREATMENT_COMPLETED"}
                for item in history
            )
        }

    @staticmethod
    def _find_existing(medical_record: dict[str, Any], idempotency_key: str) -> dict[str, Any] | None:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "DIFFERENTIAL_UPDATED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["differential"]
        return None
