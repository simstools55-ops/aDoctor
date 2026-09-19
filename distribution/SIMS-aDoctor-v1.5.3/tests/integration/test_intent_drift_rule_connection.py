from pathlib import Path
import json

from src.doctor.diagnostic_rules import (
    DiagnosticRuleEngine, DiagnosticRuleRegistry
)
from src.doctor.intent_drift import IntentDriftEngine


ROOT = Path(__file__).resolve().parents[2]


def test_intent_assessment_becomes_diagnosis_candidate():
    record = json.loads(
        (ROOT / "tests/fixtures/intent_drift/medical_record.json")
        .read_text(encoding="utf-8")
    )
    intent_policy = json.loads(
        (ROOT / "knowledge/intent_drift/intent_drift_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    record["intent_drift_assessments"].append({
        "assessment_id": "IDA-1",
        **IntentDriftEngine(intent_policy).assess(record),
    })
    rule_policy = json.loads(
        (ROOT / "knowledge/diagnostic_rules/diagnostic_rule_engine_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    registry = DiagnosticRuleRegistry.from_file(
        ROOT / "knowledge/diagnostic_rules/core_diagnostic_rules_v1.json"
    )
    result = DiagnosticRuleEngine(rule_policy).evaluate(
        record, registry.enabled_rules()
    )
    codes = [item["diagnosis_code"] for item in result["diagnosis_candidates"]]
    assert "TOPIC_DISPERSION" in codes
