from pathlib import Path
import json

from src.doctor.diagnostic_rules import DiagnosticRuleEngine, DiagnosticRuleRegistry
from src.doctor.freshness_decay import FreshnessDecayEngine


ROOT = Path(__file__).resolve().parents[2]


def test_freshness_assessment_becomes_diagnosis_candidate():
    record = json.loads(
        (ROOT / "tests/fixtures/freshness_decay/medical_record.json")
        .read_text(encoding="utf-8")
    )
    freshness_policy = json.loads(
        (ROOT / "knowledge/freshness_decay/freshness_decay_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    record["freshness_decay_assessments"].append({
        "assessment_id": "FDA-1",
        **FreshnessDecayEngine(freshness_policy).assess(record),
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
    assert "SEVERE_FRESHNESS_DECAY" in codes
