from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog


def _id(now):
    return f"FND-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class CrossArticleFindingsEngine:
    def __init__(self, event_log: MedicalRecordEventLog, rules: dict[str, Any]) -> None:
        self.event_log = event_log
        self.rules = {x["classification"]: x for x in rules["rules"]}

    def generate(self, medical_record: dict[str, Any]) -> list[dict[str, Any]]:
        observations = [
            x for x in medical_record.get("observations", [])
            if x.get("observation_type") == "CROSS_ARTICLE"
        ]
        if not observations:
            return []

        observation = observations[-1]
        created = []
        for candidate in observation["facts"]["candidates"]:
            rule = self.rules.get(candidate["classification"])
            if not rule:
                continue
            now = datetime.now(timezone.utc)
            fingerprint_source = {
                "observation_id": observation["observation_id"],
                "candidate_article_id": candidate["article"]["article_id"],
                "finding_code": rule["finding_code"],
            }
            fingerprint = hashlib.sha256(
                json.dumps(fingerprint_source, sort_keys=True).encode("utf-8")
            ).hexdigest()
            if any(x.get("fingerprint") == fingerprint for x in medical_record.get("findings", [])):
                continue

            finding = {
                "finding_id": _id(now),
                "finding_code": rule["finding_code"],
                "severity": rule["severity"],
                "confidence": rule["base_confidence"],
                "created_at": now.isoformat(),
                "evidence_ids": [],
                "vital_profile_id": (
                    medical_record["vital_profiles"][-1]["profile_id"]
                    if medical_record.get("vital_profiles") else "NOT_APPLICABLE"
                ),
                "vital_sign_code": None,
                "affected_period": {"start": "CROSS_ARTICLE", "end": "CROSS_ARTICLE"},
                "rule_version": "1.0",
                "rationale": {
                    "candidate_article_id": candidate["article"]["article_id"],
                    "classification": candidate["classification"],
                    "query_overlap_ratio": candidate["query_overlap_ratio"],
                    "title_similarity": candidate["title_similarity"],
                    "intent_similarity": candidate["intent_similarity"],
                    "dominant_article_id": candidate.get("dominant_article_id"),
                    "source_observation_id": observation["observation_id"],
                },
                "fingerprint": fingerprint,
            }
            self.event_log.append(
                medical_record,
                event_type="FINDING_RECORDED",
                payload={"finding": finding},
                occurred_at=now,
                idempotency_key=f"cross-finding:{fingerprint}",
            )
            medical_record.setdefault("findings", []).append(finding)
            created.append(finding)

        medical_record.setdefault("counters", {})["finding_count"] = len(
            medical_record.get("findings", [])
        )
        return created
