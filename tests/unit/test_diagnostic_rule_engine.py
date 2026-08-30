from pathlib import Path
import json

from src.doctor.diagnostic_rules import (
    DiagnosticRuleEngine, DiagnosticRuleRegistry
)


ROOT = Path(__file__).resolve().parents[2]


def load_record():
    return json.loads(
        (ROOT / "tests/fixtures/diagnostic_rules/medical_record.json")
        .read_text(encoding="utf-8")
    )


def engine_and_registry():
    policy = json.loads(
        (ROOT / "knowledge/diagnostic_rules/diagnostic_rule_engine_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    registry = DiagnosticRuleRegistry.from_file(
        ROOT / "knowledge/diagnostic_rules/core_diagnostic_rules_v1.json"
    )
    return DiagnosticRuleEngine(policy), registry


def test_matches_ctr_rule():
    engine, registry = engine_and_registry()
    result = engine.evaluate(load_record(), registry.enabled_rules())
    codes = [item["diagnosis_code"] for item in result["diagnosis_candidates"]]
    assert "CTR_PROBLEM" in codes


def test_mutual_exclusion_keeps_higher_priority_long_term_state():
    engine, registry = engine_and_registry()
    record = load_record()
    record["findings"].append({
        "finding_id": "FND-3",
        "finding_code": "LONG_TERM_VISIBILITY_DECAY",
        "severity": "SEVERE"
    })
    result = engine.evaluate(record, registry.enabled_rules())
    codes = [item["diagnosis_code"] for item in result["diagnosis_candidates"]]
    assert "LONG_TERM_DECAY" in codes
    assert "RECOVERY_IN_PROGRESS" not in codes


def test_low_sample_reduces_confidence():
    engine, registry = engine_and_registry()
    record = load_record()
    record["findings"][0]["low_sample"] = True
    result = engine.evaluate(record, registry.enabled_rules())
    ctr = next(
        item for item in result["diagnosis_candidates"]
        if item["diagnosis_code"] == "CTR_PROBLEM"
    )
    assert ctr["confidence"] < 70
