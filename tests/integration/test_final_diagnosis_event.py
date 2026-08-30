
from pathlib import Path
from src.doctor.diagnosis import FinalDiagnosisEngine
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
ROOT=Path(__file__).resolve().parents[2]
def eng(): return FinalDiagnosisEngine(ClinicalKnowledgeBase(ROOT/'knowledge').load(),MedicalRecordEventLog({'FINAL_DIAGNOSIS_CONFIRMED'}))
def rec(cands,findings,evidence): return {'case_id':'CASE-1','medical_record_id':'MR-1','events':[],'findings':findings,'evidence':evidence,'differential_assessments':[{'differential_id':'DIF-1','candidates':cands}],'final_diagnoses':[],'history':[],'counters':{'final_diagnosis_count':0}}
def test_final_diagnosis_event():
 r=rec([{'diagnosis_code':'CONTENT_STALE','confidence':90,'supporting_finding_ids':['F1'],'contradicting_finding_ids':[],'evidence_ids':['E1']}],[{'finding_id':'F1','finding_code':'CONTENT_OUTDATED','severity':'MODERATE','evidence_ids':['E1']}],[{'evidence_id':'E1','evidence_code':'LONG_TIME_SINCE_UPDATE','low_sample':False}]); x=eng().confirm(r,idempotency_key='x'); assert x['status']=='CONFIRMED' and r['events'][0]['event_type']=='FINAL_DIAGNOSIS_CONFIRMED'
def test_close_deferred():
 r=rec([{'diagnosis_code':'CONTENT_STALE','confidence':82,'supporting_finding_ids':['F1'],'contradicting_finding_ids':[],'evidence_ids':['E1']},{'diagnosis_code':'LOW_CTR_WITH_STRONG_POSITION','confidence':75,'supporting_finding_ids':['F2'],'contradicting_finding_ids':[],'evidence_ids':['E2']}],[{'finding_id':'F1','finding_code':'CONTENT_OUTDATED','severity':'MODERATE','evidence_ids':['E1']},{'finding_id':'F2','finding_code':'CTR_UNDERPERFORMING','severity':'MODERATE','evidence_ids':['E2']}],[{'evidence_id':'E1','evidence_code':'LONG_TIME_SINCE_UPDATE','low_sample':False},{'evidence_id':'E2','evidence_code':'CTR_BELOW_POSITION_EXPECTATION','low_sample':False}]); assert eng().confirm(r,idempotency_key='y')['defer_reason']=='CLOSE_CANDIDATES'
def test_low_sample_deferred():
 r=rec([{'diagnosis_code':'CONTENT_STALE','confidence':85,'supporting_finding_ids':['F1'],'contradicting_finding_ids':[],'evidence_ids':['E1']}],[{'finding_id':'F1','finding_code':'CONTENT_OUTDATED','severity':'MODERATE','evidence_ids':['E1']}],[{'evidence_id':'E1','evidence_code':'LONG_TIME_SINCE_UPDATE','low_sample':True}]); assert eng().confirm(r,idempotency_key='z')['defer_reason']=='LOW_SAMPLE_ONLY'
def test_idempotent():
 r=rec([{'diagnosis_code':'CONTENT_STALE','confidence':90,'supporting_finding_ids':['F1'],'contradicting_finding_ids':[],'evidence_ids':['E1']}],[{'finding_id':'F1','finding_code':'CONTENT_OUTDATED','severity':'MODERATE','evidence_ids':['E1']}],[{'evidence_id':'E1','evidence_code':'LONG_TIME_SINCE_UPDATE','low_sample':False}]); e=eng(); a=e.confirm(r,idempotency_key='i'); b=e.confirm(r,idempotency_key='i'); assert a['diagnosis_id']==b['diagnosis_id'] and len(r['final_diagnoses'])==1
