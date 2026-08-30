from pathlib import Path
import json
from src.doctor.cannibalization import CannibalizationEngine,CannibalizationService
from src.doctor.events import MedicalRecordEventLog
ROOT=Path(__file__).resolve().parents[2]
def test_recorded_idempotent():
 d=json.loads((ROOT/'tests/fixtures/cannibalization/medical_record.json').read_text());p=json.loads((ROOT/'knowledge/cannibalization/cannibalization_policy_v1.json').read_text())
 s=CannibalizationService(engine=CannibalizationEngine(p),event_log=MedicalRecordEventLog({'CANNIBALIZATION_ASSESSED'}));a=s.assess(d,idempotency_key='x');b=s.assess(d,idempotency_key='x')
 assert a['assessment_id']==b['assessment_id'];assert len(d['cannibalization_assessments'])==1
