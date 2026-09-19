from pathlib import Path
import json

from src.doctor.diagnostic_rules import (
    DiagnosticRuleEngine, DiagnosticRuleEvaluationService,
    DiagnosticRuleRegistry
)
from src.doctor.events import MedicalRecordEventLog


ROOT = Path(__file__).resolve().parents[2]


def test_evaluation_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/diagnostic_rules/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/diagnostic_rules/diagnostic_rule_engine_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    registry = DiagnosticRuleRegistry.from_file(
        ROOT / "knowledge/diagnostic_rules/core_diagnostic_rules_v1.json"
    )
    service = DiagnosticRuleEvaluationService(
        engine=DiagnosticRuleEngine(policy),
        registry=registry,
        event_log=MedicalRecordEventLog({"DIAGNOSTIC_RULES_EVALUATED"}),
    )
    first = service.evaluate(record, idempotency_key="rules:1")
    second = service.evaluate(record, idempotency_key="rules:1")

    assert first["evaluation_id"] == second["evaluation_id"]
    assert len(record["rule_evaluations"]) == 1
    assert record["counters"]["rule_evaluation_count"] == 1
