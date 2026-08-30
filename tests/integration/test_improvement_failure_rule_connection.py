from pathlib import Path
import json

from src.doctor.diagnostic_rules import (
    DiagnosticRuleEngine, DiagnosticRuleRegistry
)
from src.doctor.improvement_failure import ImprovementFailureEngine


ROOT = Path(__file__).resolve().parents[2]


def test_failure_assessment_becomes_diagnosis_candidate():
    record = json.loads(
        (ROOT / "tests/fixtures/improvement_failure/medical_record.json")
        .read_text(encoding="utf-8")
    )
    failure_policy = json.loads(
        (ROOT / "knowledge/improvement_failure/improvement_failure_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    record["improvement_failure_assessments"].append(
        {
            "assessment_id": "IFA-1",
            **ImprovementFailureEngine(failure_policy).assess(record),
        }
    )
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
    codes = [
        item["diagnosis_code"]
        for item in result["diagnosis_candidates"]
    ]
    assert "POST_IMPROVEMENT_WORSENING" in codes
