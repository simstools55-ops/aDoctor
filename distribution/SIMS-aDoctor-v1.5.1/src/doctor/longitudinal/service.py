from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .analyzer import LongitudinalAnalyzer


def _profile_id(now: datetime) -> str:
    return f"LPR-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class LongitudinalProfileService:
    def __init__(
        self,
        analyzer: LongitudinalAnalyzer,
        event_log: MedicalRecordEventLog,
    ) -> None:
        self.analyzer = analyzer
        self.event_log = event_log

    def generate(
        self,
        medical_record: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "LONGITUDINAL_PROFILE_UPDATED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["longitudinal_profile"]

        now = datetime.now(timezone.utc)
        analysis = self.analyzer.analyze(medical_record)
        patient = medical_record["patient"]

        profile = {
            "contract_name": "SIMS_DOCTOR_LONGITUDINAL_PROFILE_V1",
            "contract_version": "1.0",
            "profile_id": _profile_id(now),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "article": {
                "site_id": patient["site_id"],
                "article_id": patient["article_id"],
                "url": patient["article_url"],
                "title": patient.get("article_title", ""),
            },
            "generated_at": now.isoformat(),
            **analysis,
        }
        profile["fingerprint"] = hashlib.sha256(
            json.dumps(
                {
                    "diagnosis_ids": profile["trace"]["diagnosis_ids"],
                    "treatment_history_observation_ids":
                        profile["trace"]["treatment_history_observation_ids"],
                    "profile_status": profile["profile_status"],
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        self.event_log.append(
            medical_record,
            event_type="LONGITUDINAL_PROFILE_UPDATED",
            payload={"longitudinal_profile": profile},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("longitudinal_profiles", []).append(profile)
        medical_record.setdefault("counters", {})["longitudinal_profile_count"] = len(
            medical_record["longitudinal_profiles"]
        )
        medical_record["updated_at"] = now.isoformat()
        return profile
