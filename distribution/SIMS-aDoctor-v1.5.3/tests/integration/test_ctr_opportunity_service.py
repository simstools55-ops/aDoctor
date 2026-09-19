from pathlib import Path
import json
from src.doctor.ctr_opportunity import CtrOpportunityEngine,CtrOpportunityService
from src.doctor.events import MedicalRecordEventLog
ROOT=Path(__file__).resolve().parents[2]
def test_recorded_idempotent():
    d=json.loads((ROOT/"tests/fixtures/ctr_opportunity/medical_record.json").read_text(encoding="utf-8"))
    p=json.loads((ROOT/"knowledge/ctr_opportunity/ctr_opportunity_policy_v1.json").read_text(encoding="utf-8"))
    s=CtrOpportunityService(engine=CtrOpportunityEngine(p),event_log=MedicalRecordEventLog({"CTR_OPPORTUNITY_ASSESSED"}))
    a=s.assess(d,idempotency_key="x"); b=s.assess(d,idempotency_key="x")
    assert a["assessment_id"]==b["assessment_id"]; assert len(d["ctr_opportunity_assessments"])==1
