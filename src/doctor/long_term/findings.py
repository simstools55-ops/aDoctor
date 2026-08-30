from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets


def _id(now):
    return f"FND-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class LongTermFindingsEngine:
    MAP = {
        "LONG_TERM_VISIBILITY_DECLINE": "LONG_TERM_VISIBILITY_DECAY",
        "LONG_TERM_CTR_DECAY": "LONG_TERM_CTR_DECAY",
        "LONG_TERM_POSITION_DECAY": "LONG_TERM_POSITION_DECAY",
        "SEASONAL_PATTERN_OBSERVED": "SEASONALITY_DETECTED",
        "LONG_TERM_RECOVERY_OBSERVED": "RECOVERY_TREND",
    }

    def __init__(self, event_log):
        self.event_log = event_log

    def generate(self, medical_record):
        created = []
        for evidence in medical_record.get("evidence", []):
            finding_code = self.MAP.get(evidence["evidence_code"])
            if not finding_code:
                continue
            measured = evidence["measured_values"]
            severity = self._severity(evidence["evidence_code"], measured)
            now = datetime.now(timezone.utc)
            fingerprint = hashlib.sha256(json.dumps({
                "finding_code": finding_code,
                "evidence_id": evidence["evidence_id"],
                "severity": severity,
            }, sort_keys=True).encode("utf-8")).hexdigest()

            if any(x.get("fingerprint") == fingerprint for x in medical_record.get("findings", [])):
                continue

            item = {
                "finding_id": _id(now),
                "finding_code": finding_code,
                "severity": severity,
                "confidence": 60 if evidence.get("low_sample") else 85,
                "created_at": now.isoformat(),
                "evidence_ids": [evidence["evidence_id"]],
                "vital_profile_id": (
                    medical_record["vital_profiles"][-1]["profile_id"]
                    if medical_record.get("vital_profiles") else "NOT_APPLICABLE"
                ),
                "vital_sign_code": None,
                "affected_period": {"start": "365_DAY_HISTORY", "end": "CURRENT"},
                "rule_version": "1.0",
                "rationale": {
                    "classification": measured["classification"],
                    "visibility_change_ratio": measured.get("visibility_change_ratio"),
                    "ctr_change_ratio": measured.get("ctr_change_ratio"),
                    "position_change": measured.get("position_change"),
                    "seasonality_score": measured.get("seasonality_score"),
                    "low_sample": evidence.get("low_sample"),
                },
                "fingerprint": fingerprint,
            }
            self.event_log.append(
                medical_record,
                event_type="FINDING_RECORDED",
                payload={"finding": item},
                occurred_at=now,
                idempotency_key=f"long-term-finding:{fingerprint}",
            )
            medical_record.setdefault("findings", []).append(item)
            created.append(item)

        medical_record.setdefault("counters", {})["finding_count"] = len(medical_record.get("findings", []))
        return created

    @staticmethod
    def _severity(code, measured):
        if code == "LONG_TERM_VISIBILITY_DECLINE":
            ratio = abs(measured.get("visibility_change_ratio", 0))
            return "CRITICAL" if ratio >= 0.6 else "SEVERE" if ratio >= 0.4 else "MODERATE"
        if code in {"LONG_TERM_CTR_DECAY", "LONG_TERM_POSITION_DECAY"}:
            return "SEVERE" if abs(measured.get("ctr_change_ratio", 0)) >= 0.5 else "MODERATE"
        if code == "SEASONAL_PATTERN_OBSERVED":
            return "INFO"
        if code == "LONG_TERM_RECOVERY_OBSERVED":
            return "MILD"
        return "MILD"
