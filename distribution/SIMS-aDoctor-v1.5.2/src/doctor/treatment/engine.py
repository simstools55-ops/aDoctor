from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase


class TreatmentRecommendationError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _id(now: datetime) -> str:
    return f"TRT-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class TreatmentRecommendationEngine:
    def __init__(self, ckb: ClinicalKnowledgeBase, event_log: MedicalRecordEventLog) -> None:
        self.ckb = ckb
        self.event_log = event_log

    def recommend(self, medical_record: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        existing = self._find_existing(medical_record, idempotency_key)
        if existing is not None:
            return existing

        diagnoses = medical_record.get("final_diagnoses", [])
        if not diagnoses:
            raise TreatmentRecommendationError("Final diagnosis is missing")
        diagnosis = diagnoses[-1]

        rule = None
        if diagnosis["status"] == "CONFIRMED":
            for item in self.ckb.treatment_rules():
                if item["diagnosis_code"] == diagnosis["diagnosis_code"]:
                    rule = item
                    break
        else:
            for item in self.ckb.deferred_treatment_rules():
                if item["defer_reason"] == diagnosis["defer_reason"]:
                    rule = item
                    break

        if rule is None:
            raise TreatmentRecommendationError("No treatment rule matches the diagnosis result")

        now = datetime.now(timezone.utc)
        payload = {
            "diagnosis_id": diagnosis["diagnosis_id"],
            "diagnosis_status": diagnosis["status"],
            "diagnosis_code": diagnosis.get("diagnosis_code"),
            "defer_reason": diagnosis.get("defer_reason"),
            "treatment_code": rule["treatment_code"],
            "target": rule["target"],
            "priority": rule["priority"],
            "created_at": now.isoformat(),
            "rule_version": "1.0",
        }
        payload["fingerprint"] = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
        payload["treatment_recommendation_id"] = _id(now)

        self.event_log.append(
            medical_record,
            event_type="TREATMENT_RECOMMENDED",
            payload={"treatment_recommendation": payload},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("treatment_recommendations", []).append(payload)
        medical_record.setdefault("counters", {})["treatment_recommendation_count"] = len(
            medical_record["treatment_recommendations"]
        )
        medical_record["updated_at"] = now.isoformat()
        return payload

    @staticmethod
    def _find_existing(medical_record: dict[str, Any], idempotency_key: str) -> dict[str, Any] | None:
        for event in medical_record.get("events", []):
            if event.get("event_type") == "TREATMENT_RECOMMENDED" and event.get("idempotency_key") == idempotency_key:
                return event["payload"]["treatment_recommendation"]
        return None
