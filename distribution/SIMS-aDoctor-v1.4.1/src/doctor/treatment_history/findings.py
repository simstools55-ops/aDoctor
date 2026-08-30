from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets


def _id(now):
    return f"FND-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class TreatmentHistoryFindingsEngine:
    MAP = {
        "TREATMENT_EFFECT_POSITIVE": "IMPROVEMENT_CONFIRMED",
        "TREATMENT_NO_EFFECT": "TREATMENT_INEFFECTIVE",
        "POST_TREATMENT_WORSENING": "POST_TREATMENT_WORSENING",
        "TREATMENT_MIXED_RESPONSE": "MIXED_TREATMENT_RESPONSE",
        "TREATMENT_FOLLOW_UP_INSUFFICIENT": "FOLLOW_UP_INSUFFICIENT",
    }

    def __init__(self, event_log):
        self.event_log = event_log

    def generate(self, medical_record):
        created = []
        for evidence in medical_record.get("evidence", []):
            finding_code = self.MAP.get(evidence["evidence_code"])
            if not finding_code:
                continue
            now = datetime.now(timezone.utc)
            severity = self._severity(finding_code, evidence["measured_values"])
            fingerprint = hashlib.sha256(json.dumps({
                "finding_code": finding_code,
                "evidence_id": evidence["evidence_id"],
                "severity": severity,
            }, sort_keys=True).encode("utf-8")).hexdigest()
            if any(item.get("fingerprint") == fingerprint for item in medical_record.get("findings", [])):
                continue

            finding = {
                "finding_id": _id(now),
                "finding_code": finding_code,
                "severity": severity,
                "confidence": 60 if evidence.get("low_sample") else 90,
                "created_at": now.isoformat(),
                "evidence_ids": [evidence["evidence_id"]],
                "vital_profile_id": (
                    medical_record["vital_profiles"][-1]["profile_id"]
                    if medical_record.get("vital_profiles") else "NOT_APPLICABLE"
                ),
                "vital_sign_code": None,
                "affected_period": {
                    "start": evidence["comparison_basis"]["baseline_period"],
                    "end": evidence["comparison_basis"]["current_period"],
                },
                "rule_version": "1.0",
                "rationale": dict(evidence["measured_values"]),
                "fingerprint": fingerprint,
            }
            self.event_log.append(
                medical_record,
                event_type="FINDING_RECORDED",
                payload={"finding": finding},
                occurred_at=now,
                idempotency_key=f"treatment-finding:{fingerprint}",
            )
            medical_record.setdefault("findings", []).append(finding)
            created.append(finding)
        medical_record.setdefault("counters", {})["finding_count"] = len(
            medical_record.get("findings", [])
        )
        return created

    @staticmethod
    def _severity(code, measured):
        if code == "POST_TREATMENT_WORSENING":
            score = measured.get("effect_score", 0)
            return "CRITICAL" if score <= -0.35 else "SEVERE"
        if code == "TREATMENT_INEFFECTIVE":
            return "MODERATE"
        if code == "MIXED_TREATMENT_RESPONSE":
            return "MILD"
        return "INFO"
