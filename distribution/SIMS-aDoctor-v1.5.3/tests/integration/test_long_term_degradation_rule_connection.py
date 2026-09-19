from pathlib import Path
import json

from src.doctor.diagnostic_rules import (
    DiagnosticRuleEngine, DiagnosticRuleRegistry
)
from src.doctor.long_term_degradation import LongTermDegradationEngine


ROOT = Path(__file__).resolve().parents[2]


def test_long_term_assessment_becomes_diagnosis_candidate():
    record = json.loads(
        (ROOT / "tests/fixtures/long_term_degradation/medical_record.json")
        .read_text(encoding="utf-8")
    )
    long_policy = json.loads(
        (ROOT / "knowledge/long_term_degradation/long_term_degradation_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    record["long_term_degradation_assessments"].append({
        "assessment_id": "LDA-1",
        **LongTermDegradationEngine(long_policy).assess(record),
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
    assert "LONG_TERM_DECAY" in codes
