from pathlib import Path
import json
from src.doctor.ctr_opportunity import CtrOpportunityEngine
from src.doctor.diagnostic_rules import DiagnosticRuleEngine,DiagnosticRuleRegistry
ROOT=Path(__file__).resolve().parents[2]
def test_rule_connection():
    d=json.loads((ROOT/"tests/fixtures/ctr_opportunity/medical_record.json").read_text(encoding="utf-8"))
    p=json.loads((ROOT/"knowledge/ctr_opportunity/ctr_opportunity_policy_v1.json").read_text(encoding="utf-8"))
    d["ctr_opportunity_assessments"].append({"assessment_id":"CTA-1",**CtrOpportunityEngine(p).assess(d)})
    rp=json.loads((ROOT/"knowledge/diagnostic_rules/diagnostic_rule_engine_policy_v1.json").read_text(encoding="utf-8"))
    reg=DiagnosticRuleRegistry.from_file(ROOT/"knowledge/diagnostic_rules/core_diagnostic_rules_v1.json")
    r=DiagnosticRuleEngine(rp).evaluate(d,reg.enabled_rules())
    assert "CTR_OPPORTUNITY" in [x["diagnosis_code"] for x in r["diagnosis_candidates"]]
