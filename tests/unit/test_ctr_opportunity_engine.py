from pathlib import Path
import json
from src.doctor.ctr_opportunity import CtrOpportunityEngine
ROOT=Path(__file__).resolve().parents[2]
def load(): return json.loads((ROOT/"tests/fixtures/ctr_opportunity/medical_record.json").read_text(encoding="utf-8"))
def policy(): return json.loads((ROOT/"knowledge/ctr_opportunity/ctr_opportunity_policy_v1.json").read_text(encoding="utf-8"))
def test_high_opportunity():
    r=CtrOpportunityEngine(policy()).assess(load()); assert r["classification"]=="HIGH_CTR_OPPORTUNITY"; assert r["protections"]["body_rewrite_allowed"] is False
def test_winner_protected():
    d=load(); d["observations"][0]["facts"]["queries"]=[{"query":"winner","clicks":15},{"query":"other","clicks":5}]
    r=CtrOpportunityEngine(policy()).assess(d); assert r["classification"]=="WINNER_QUERY_PROTECTED"
def test_low_sample():
    d=load(); d["observations"][0]["facts"]["metrics"]["low_sample"]=True
    assert CtrOpportunityEngine(policy()).assess(d)["classification"]=="INSUFFICIENT_DATA"
