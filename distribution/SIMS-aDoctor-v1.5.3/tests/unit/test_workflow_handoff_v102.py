from src.doctor.output.case_result_v2 import CaseResultV2Builder

def test_workflow_handoff_writer_request():
    record={
      "case_id":"C1","medical_record_id":"M1",
      "patient":{"site_id":"S","article_id":"A","article_url":"https://example.com/a","article_title":"T"},
      "final_diagnoses":[{"status":"CONFIRMED","diagnosis_code":"X","diagnosis_id":"D1","confidence":80}],
      "treatment_recommendations":[{"target":"WRITER","treatment_code":"LIMITED","priority":"HIGH","recommended_scope":["内部リンク追加"],"prohibited_actions":["全面リライト"],"dependencies":[]}],
      "workflow":{}
    }
    result=CaseResultV2Builder().build(record)
    h=result["workflow_handoff"]
    assert h["treatment_class"] == "限定修正"
    assert h["writer_request_text"] is None
    assert h["handoff_mode"] == "RETURN_TO_SBM_FOR_REFERRAL"
    assert h["creator_request_text"] is None
