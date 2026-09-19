from pathlib import Path
import json

from src.doctor.diagnostic_rules import DiagnosticRuleRegistry


ROOT = Path(__file__).resolve().parents[2]


def test_loads_rule_registry():
    registry = DiagnosticRuleRegistry.from_file(
        ROOT / "knowledge/diagnostic_rules/core_diagnostic_rules_v1.json"
    )
    enabled = registry.enabled_rules()
    assert len(enabled) >= 10
    rule_ids = {rule.rule_id for rule in enabled}
    assert {"DR-CTR-001", "DR-LONG-001", "DR-RECOVERY-001"}.issubset(rule_ids)
    assert {
        "DR-IMPROVEMENT-FAILURE-001",
        "DR-IMPROVEMENT-WORSENING-001",
        "DR-IMPROVEMENT-FOLLOWUP-001",
    }.issubset(rule_ids)
    assert {
        "DR-LONGTERM-CHRONIC-001",
        "DR-LONGTERM-SEASONAL-001",
        "DR-LONGTERM-RECOVERY-001",
        "DR-LONGTERM-FOLLOWUP-001",
    }.issubset(rule_ids)
