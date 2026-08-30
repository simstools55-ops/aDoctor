from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets


def _id(now):
    return f"EVD-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class LongTermEvidenceEngine:
    MAP = {
        "GRADUAL_DECLINE": "LONG_TERM_VISIBILITY_DECLINE",
        "SHARP_DECLINE": "LONG_TERM_VISIBILITY_DECLINE",
        "CTR_DECAY": "LONG_TERM_CTR_DECAY",
        "POSITION_DECAY": "LONG_TERM_POSITION_DECAY",
        "SEASONAL_PATTERN": "SEASONAL_PATTERN_OBSERVED",
        "RECOVERY": "LONG_TERM_RECOVERY_OBSERVED",
    }

    def __init__(self, event_log):
        self.event_log = event_log

    def extract(self, medical_record):
        observations = [x for x in medical_record.get("observations", []) if x.get("observation_type") == "LONG_TERM"]
        if not observations:
            return []
        observation = observations[-1]
        trend = observation["facts"]["trend"]
        code = self.MAP.get(trend["classification"])
        if not code:
            return []

        now = datetime.now(timezone.utc)
        measured = dict(trend)
        fingerprint = hashlib.sha256(json.dumps({
            "code": code,
            "observation_id": observation["observation_id"],
            "measured": measured,
        }, sort_keys=True).encode("utf-8")).hexdigest()

        if any(x.get("fingerprint") == fingerprint for x in medical_record.get("evidence", [])):
            return []

        item = {
            "evidence_id": _id(now),
            "evidence_code": code,
            "created_at": now.isoformat(),
            "source_observation_ids": [observation["observation_id"]],
            "measured_values": measured,
            "comparison_basis": {"window_count": len(observation["facts"]["windows"])},
            "rule_version": "1.0",
            "low_sample": bool(trend.get("low_sample")),
            "fingerprint": fingerprint,
        }
        self.event_log.append(
            medical_record,
            event_type="EVIDENCE_RECORDED",
            payload={"evidence": item},
            occurred_at=now,
            idempotency_key=f"long-term-evidence:{fingerprint}",
        )
        medical_record.setdefault("evidence", []).append(item)
        medical_record.setdefault("counters", {})["evidence_count"] = len(medical_record["evidence"])
        return [item]
