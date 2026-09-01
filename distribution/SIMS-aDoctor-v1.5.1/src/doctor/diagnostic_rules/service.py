from __future__ import annotations

from datetime import datetime, timezone
import secrets
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .engine import DiagnosticRuleEngine
from .registry import DiagnosticRuleRegistry


def _evaluation_id(now):
    return f"RUL-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class DiagnosticRuleEvaluationService:
    def __init__(
        self,
        *,
        engine: DiagnosticRuleEngine,
        registry: DiagnosticRuleRegistry,
        event_log: MedicalRecordEventLog,
    ) -> None:
        self.engine = engine
        self.registry = registry
        self.event_log = event_log

    def evaluate(
        self,
        medical_record: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "DIAGNOSTIC_RULES_EVALUATED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["rule_evaluation"]

        now = datetime.now(timezone.utc)
        evaluated = self.engine.evaluate(
            medical_record,
            self.registry.enabled_rules(),
        )
        result = {
            "contract_name": "SIMS_DOCTOR_RULE_EVALUATION_RESULT_V1",
            "contract_version": "1.0",
            "evaluation_id": _evaluation_id(now),
            "case_id": medical_record["case_id"],
            "evaluated_at": now.isoformat(),
            **evaluated,
        }
        self.event_log.append(
            medical_record,
            event_type="DIAGNOSTIC_RULES_EVALUATED",
            payload={"rule_evaluation": result},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("rule_evaluations", []).append(result)
        medical_record.setdefault("counters", {})["rule_evaluation_count"] = len(
            medical_record["rule_evaluations"]
        )
        medical_record["updated_at"] = now.isoformat()
        return result
