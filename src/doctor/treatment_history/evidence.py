from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets


def _id(now):
    return f"EVD-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class TreatmentHistoryEvidenceEngine:
    CODE_MAP = {
        "IMPROVED": "TREATMENT_EFFECT_POSITIVE",
        "PARTIAL_IMPROVEMENT": "TREATMENT_EFFECT_POSITIVE",
        "NO_EFFECT": "TREATMENT_NO_EFFECT",
        "WORSENED": "POST_TREATMENT_WORSENING",
        "MIXED_RESPONSE": "TREATMENT_MIXED_RESPONSE",
        "INSUFFICIENT_FOLLOW_UP": "TREATMENT_FOLLOW_UP_INSUFFICIENT",
    }

    def __init__(self, event_log):
        self.event_log = event_log

    def extract(self, medical_record):
        observations = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") == "TREATMENT_HISTORY"
        ]
        if not observations:
            return []
        observation = observations[-1]
        assessment = observation["facts"]["assessment"]
        code = self.CODE_MAP[assessment["classification"]]
        now = datetime.now(timezone.utc)
        fingerprint = hashlib.sha256(json.dumps({
            "code": code,
            "observation_id": observation["observation_id"],
            "assessment": assessment,
        }, sort_keys=True).encode("utf-8")).hexdigest()
        if any(item.get("fingerprint") == fingerprint for item in medical_record.get("evidence", [])):
            return []

        evidence = {
            "evidence_id": _id(now),
            "evidence_code": code,
            "created_at": now.isoformat(),
            "source_observation_ids": [observation["observation_id"]],
            "measured_values": dict(assessment),
            "comparison_basis": {
                "treatment_id": observation["facts"]["treatment"]["treatment_id"],
                "baseline_period": observation["facts"]["baseline"]["start_date"],
                "current_period": observation["facts"]["checkpoints"][-1]["end_date"],
            },
            "rule_version": "1.0",
            "low_sample": bool(assessment.get("low_sample")),
            "fingerprint": fingerprint,
        }
        self.event_log.append(
            medical_record,
            event_type="EVIDENCE_RECORDED",
            payload={"evidence": evidence},
            occurred_at=now,
            idempotency_key=f"treatment-evidence:{fingerprint}",
        )
        medical_record.setdefault("evidence", []).append(evidence)
        medical_record.setdefault("counters", {})["evidence_count"] = len(
            medical_record["evidence"]
        )
        return [evidence]
