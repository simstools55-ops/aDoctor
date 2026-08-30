from pathlib import Path
import json
from src.doctor.cannibalization import CannibalizationEngine
from src.doctor.diagnostic_rules import DiagnosticRuleEngine,DiagnosticRuleRegistry
ROOT=Path(__file__).resolve().parents[2]
def test_rule_connection():
 d=json.loads((ROOT/'tests/fixtures/cannibalization/medical_record.json').read_text());p=json.loads((ROOT/'knowledge/cannibalization/cannibalization_policy_v1.json').read_text());d['cannibalization_assessments'].append({'assessment_id':'CAA-1',**CannibalizationEngine(p).assess(d)})
 rp=json.loads((ROOT/'knowledge/diagnostic_rules/diagnostic_rule_engine_policy_v1.json').read_text());reg=DiagnosticRuleRegistry.from_file(ROOT/'knowledge/diagnostic_rules/core_diagnostic_rules_v1.json');r=DiagnosticRuleEngine(rp).evaluate(d,reg.enabled_rules())
 assert 'MERGE_CANDIDATE' in [x['diagnosis_code'] for x in r['diagnosis_candidates']]
