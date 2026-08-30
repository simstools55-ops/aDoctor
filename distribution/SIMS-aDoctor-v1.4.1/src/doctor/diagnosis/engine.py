
from datetime import datetime,timedelta,timezone
import hashlib,json,secrets
from typing import Any
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from .models import FinalDiagnosisRecord
class FinalDiagnosisError(ValueError): pass
SEVERITY_ORDER={'INFO':0,'MILD':1,'MODERATE':2,'SEVERE':3,'CRITICAL':4}
def _canonical(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def _id(now): return f"DX-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"
class FinalDiagnosisEngine:
    def __init__(self,ckb:ClinicalKnowledgeBase,event_log:MedicalRecordEventLog):
        self.ckb=ckb; self.event_log=event_log; self.rules=ckb.final_diagnosis_rules(); self.policy=ckb.final_diagnosis_global_policy()
    def confirm(self,medical_record:dict[str,Any],*,idempotency_key:str)->dict[str,Any]:
        for e in medical_record.get('events',[]):
            if e.get('event_type')=='FINAL_DIAGNOSIS_CONFIRMED' and e.get('idempotency_key')==idempotency_key: return e['payload']['final_diagnosis']
        latest=(medical_record.get('differential_assessments') or [None])[-1]; candidates=latest.get('candidates',[]) if latest else []; top=candidates[0] if candidates else None
        findings={x['finding_id']:x for x in medical_record.get('findings',[])}; evidence={x['evidence_id']:x for x in medical_record.get('evidence',[])}
        now=datetime.now(timezone.utc); checks=[]; reason=None; rule=self.rules.get(top['diagnosis_code']) if top else None
        if not top: checks.append({'check':'CANDIDATE_EXISTS','passed':False}); reason='NO_CANDIDATE'
        else: checks.append({'check':'CANDIDATE_EXISTS','passed':True})
        if top and not rule: raise FinalDiagnosisError('No final diagnosis rule')
        if top and rule.get('force_status')=='DEFERRED': reason='INSUFFICIENT_DATA'
        if top and reason is None:
            ok=top['confidence']>=self.policy['minimum_confirmation_confidence']; checks.append({'check':'MINIMUM_CONFIDENCE','passed':ok,'actual':top['confidence'],'required':self.policy['minimum_confirmation_confidence']});
            if not ok: reason='LOW_CONFIDENCE'
        if top and reason is None and len(candidates)>1:
            margin=top['confidence']-candidates[1]['confidence']; ok=margin>=self.policy['minimum_margin_to_second_candidate']; checks.append({'check':'CANDIDATE_MARGIN','passed':ok,'actual':margin,'required':self.policy['minimum_margin_to_second_candidate']});
            if not ok: reason='CLOSE_CANDIDATES'
        sf=tuple(top.get('supporting_finding_ids',[])) if top else (); cf=tuple(top.get('contradicting_finding_ids',[])) if top else (); eids=tuple(top.get('evidence_ids',[])) if top else ()
        sfind=[findings[i] for i in sf if i in findings]; sevd=[evidence[i] for i in eids if i in evidence]
        if top and reason is None:
            low=bool(sevd) and all(x.get('low_sample') for x in sevd); checks.append({'check':'NOT_LOW_SAMPLE_ONLY','passed':not low});
            if low: reason='LOW_SAMPLE_ONLY'
        if top and reason is None:
            have={x['evidence_code'] for x in sevd}; miss=[c for c in rule.get('required_evidence',[]) if c not in have]; checks.append({'check':'REQUIRED_EVIDENCE','passed':not miss,'missing':miss});
            if miss: reason='MISSING_EVIDENCE'
        if top and reason is None:
            have={x['finding_code'] for x in sfind}; miss=[c for c in rule.get('required_findings',[]) if c not in have]; checks.append({'check':'REQUIRED_FINDINGS','passed':not miss,'missing':miss});
            if miss: reason='MISSING_FINDINGS'
        if top and reason is None:
            ctx={'history.improvement_event_exists':any(x.get('event_type') in {'IMPROVEMENT_RECORDED','TREATMENT_COMPLETED'} for x in medical_record.get('history',[]))}; miss=[k for k in rule.get('required_context',[]) if not ctx.get(k,False)]; checks.append({'check':'REQUIRED_CONTEXT','passed':not miss,'missing':miss});
            if miss: reason='MISSING_CONTEXT'
        if top and reason is None and cf:
            ok=not(self.policy['contradiction_behavior']=='DEFER_IF_PRESENT_AND_TOP_CONFIDENCE_BELOW_90' and top['confidence']<90); checks.append({'check':'CONTRADICTION','passed':ok,'count':len(cf)});
            if not ok: reason='CONTRADICTION'
        status='DEFERRED' if reason else 'CONFIRMED'; code=rule['final_diagnosis_code'] if status=='CONFIRMED' else None
        sev=None
        if status=='CONFIRMED':
            vals=[x['severity'] for x in sfind if x['finding_code'] in set(rule.get('severity_source',[]))]; sev=max(vals,key=lambda x:SEVERITY_ORDER[x]) if vals else None
        rev=self.policy['review_days']['CONFIRMED_DEFAULT'] if status=='CONFIRMED' else self.policy['review_days'].get({'LOW_SAMPLE_ONLY':'DEFERRED_LOW_SAMPLE','INSUFFICIENT_DATA':'DEFERRED_LOW_SAMPLE','CLOSE_CANDIDATES':'DEFERRED_CLOSE_CANDIDATES','LOW_CONFIDENCE':'DEFERRED_LOW_CONFIDENCE','MISSING_EVIDENCE':'DEFERRED_MISSING_EVIDENCE','MISSING_FINDINGS':'DEFERRED_MISSING_EVIDENCE','MISSING_CONTEXT':'DEFERRED_MISSING_EVIDENCE','CONTRADICTION':'DEFERRED_CONTRADICTION','NO_CANDIDATE':'DEFERRED_NO_CANDIDATE'}.get(reason,'DEFERRED_NO_CANDIDATE'),30)
        fp=hashlib.sha256(_canonical({'status':status,'code':code,'candidate':top['diagnosis_code'] if top else None,'differential_id':latest['differential_id'] if latest else None,'reason':reason}).encode()).hexdigest()
        rec=FinalDiagnosisRecord(_id(now),status,code,top['diagnosis_code'] if top else None,top['confidence'] if top else None,sev,now,rev,now+timedelta(days=rev),latest['differential_id'] if latest else None,sf,cf,eids,tuple(checks),reason,'1.0',fp)
        data=rec.to_dict(); self.event_log.append(medical_record,event_type='FINAL_DIAGNOSIS_CONFIRMED',payload={'final_diagnosis':data},occurred_at=now,idempotency_key=idempotency_key); medical_record.setdefault('final_diagnoses',[]).append(data); medical_record.setdefault('counters',{})['final_diagnosis_count']=len(medical_record['final_diagnoses']); medical_record['case_status']='DIAGNOSED' if status=='CONFIRMED' else 'FOLLOW_UP'; medical_record['updated_at']=now.isoformat(); return data
