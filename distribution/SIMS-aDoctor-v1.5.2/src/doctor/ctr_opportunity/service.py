from datetime import datetime, timezone
import secrets
class CtrOpportunityService:
    def __init__(self,*,engine,event_log): self.engine=engine; self.event_log=event_log
    def assess(self,medical_record,*,idempotency_key):
        for e in medical_record.get("events",[]):
            if e.get("event_type")=="CTR_OPPORTUNITY_ASSESSED" and e.get("idempotency_key")==idempotency_key:
                return e["payload"]["ctr_opportunity_assessment"]
        now=datetime.now(timezone.utc)
        result={"contract_name":"SIMS_DOCTOR_CTR_OPPORTUNITY_ASSESSMENT_V1","contract_version":"1.0","assessment_id":f"CTA-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}","case_id":medical_record["case_id"],"medical_record_id":medical_record["medical_record_id"],"assessed_at":now.isoformat(),**self.engine.assess(medical_record)}
        self.event_log.append(medical_record,event_type="CTR_OPPORTUNITY_ASSESSED",payload={"ctr_opportunity_assessment":result},occurred_at=now,idempotency_key=idempotency_key)
        medical_record.setdefault("ctr_opportunity_assessments",[]).append(result)
        medical_record.setdefault("counters",{})["ctr_opportunity_assessment_count"]=len(medical_record["ctr_opportunity_assessments"])
        medical_record["updated_at"]=now.isoformat(); return result
