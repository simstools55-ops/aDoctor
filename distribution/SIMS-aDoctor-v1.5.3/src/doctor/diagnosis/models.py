
from dataclasses import dataclass
from datetime import datetime
from typing import Any
@dataclass(frozen=True)
class FinalDiagnosisRecord:
    diagnosis_id:str; status:str; diagnosis_code:str|None; source_candidate_code:str|None; confidence:int|None; severity:str|None; diagnosed_at:datetime; recommended_review_days:int; review_due_at:datetime; differential_id:str|None; supporting_finding_ids:tuple[str,...]; contradicting_finding_ids:tuple[str,...]; evidence_ids:tuple[str,...]; validation_checks:tuple[dict[str,Any],...]; defer_reason:str|None; rule_version:str; fingerprint:str
    def to_dict(self):
        return {'diagnosis_id':self.diagnosis_id,'status':self.status,'diagnosis_code':self.diagnosis_code,'source_candidate_code':self.source_candidate_code,'confidence':self.confidence,'severity':self.severity,'diagnosed_at':self.diagnosed_at.isoformat(),'recommended_review_days':self.recommended_review_days,'review_due_at':self.review_due_at.isoformat(),'differential_id':self.differential_id,'supporting_finding_ids':list(self.supporting_finding_ids),'contradicting_finding_ids':list(self.contradicting_finding_ids),'evidence_ids':list(self.evidence_ids),'validation_checks':list(self.validation_checks),'defer_reason':self.defer_reason,'rule_version':self.rule_version,'fingerprint':self.fingerprint}
