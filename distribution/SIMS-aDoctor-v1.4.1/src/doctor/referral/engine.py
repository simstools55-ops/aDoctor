from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase


class ReferralError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _id(now: datetime) -> str:
    return f"REF-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class ReferralEngine:
    def __init__(self, ckb: ClinicalKnowledgeBase, event_log: MedicalRecordEventLog) -> None:
        self.ckb = ckb
        self.event_log = event_log

    def issue(self, medical_record: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        existing = self._find_existing(medical_record, idempotency_key)
        if existing is not None:
            return existing

        recommendations = medical_record.get("treatment_recommendations", [])
        diagnoses = medical_record.get("final_diagnoses", [])
        if not recommendations or not diagnoses:
            raise ReferralError("Diagnosis and treatment recommendation are required")

        recommendation = recommendations[-1]
        diagnosis = diagnoses[-1]
        target = recommendation["target"]
        if target not in self.ckb.referral_targets():
            raise ReferralError(f"Unsupported referral target: {target}")

        policies = self.ckb.referral_policies()
        if (
            diagnosis["status"] == "DEFERRED"
            and target in {"WRITER", "CREATOR", "MERGE"}
            and policies["deferred_diagnosis_cannot_route_to_writer_creator_merge"]
        ):
            raise ReferralError("Deferred diagnosis cannot be referred for treatment")

        now = datetime.now(timezone.utc)
        patient = medical_record["patient"]
        referral = {
            "referral_id": _id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "diagnosis_id": diagnosis["diagnosis_id"],
            "treatment_recommendation_id": recommendation["treatment_recommendation_id"],
            "target": target,
            "priority": recommendation["priority"],
            "article": {
                "site_id": patient["site_id"],
                "article_id": patient["article_id"],
                "url": patient["article_url"],
                "title": patient["article_title"],
            },
            "clinical_summary": {
                "diagnosis_status": diagnosis["status"],
                "diagnosis_code": diagnosis.get("diagnosis_code"),
                "confidence": diagnosis.get("confidence"),
                "severity": diagnosis.get("severity"),
                "defer_reason": diagnosis.get("defer_reason"),
                "treatment_code": recommendation["treatment_code"],
                "supporting_finding_ids": diagnosis.get("supporting_finding_ids", []),
                "evidence_ids": diagnosis.get("evidence_ids", []),
            },
            "issued_at": now.isoformat(),
            "contract_version": "1.0",
        }
        referral["fingerprint"] = hashlib.sha256(_canonical(referral).encode("utf-8")).hexdigest()

        self.event_log.append(
            medical_record,
            event_type="REFERRAL_ISSUED",
            payload={"referral": referral},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("referrals", []).append(referral)
        medical_record.setdefault("counters", {})["referral_count"] = len(medical_record["referrals"])
        medical_record["case_status"] = "REFERRED" if target != "OBSERVATION" else "FOLLOW_UP"
        medical_record["updated_at"] = now.isoformat()
        return referral

    @staticmethod
    def _find_existing(medical_record: dict[str, Any], idempotency_key: str) -> dict[str, Any] | None:
        for event in medical_record.get("events", []):
            if event.get("event_type") == "REFERRAL_ISSUED" and event.get("idempotency_key") == idempotency_key:
                return event["payload"]["referral"]
        return None
