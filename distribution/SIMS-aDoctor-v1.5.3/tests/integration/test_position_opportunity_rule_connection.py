from pathlib import Path
import json

from src.doctor.diagnostic_rules import (
    DiagnosticRuleEngine, DiagnosticRuleRegistry
)
from src.doctor.position_opportunity import PositionOpportunityEngine


ROOT = Path(__file__).resolve().parents[2]


def test_position_assessment_becomes_diagnosis_candidate():
    record = json.loads(
        (ROOT / "tests/fixtures/position_opportunity/medical_record.json")
        .read_text(encoding="utf-8")
    )
    position_policy = json.loads(
        (ROOT / "knowledge/position_opportunity/position_opportunity_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    record["position_opportunity_assessments"].append({
        "assessment_id": "POA-1",
        **PositionOpportunityEngine(position_policy).assess(record),
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
    assert "POSITION_OPPORTUNITY" in codes
