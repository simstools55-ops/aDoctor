from doctor.output.case_result_v2 import CaseResultV2Builder

def test_result_returns_to_sbm_without_direct_writer_request():
    record={
      "case_id":"CASE-X", "medical_record_id":"MR-X",
      "patient":{"site_id":"SITE","article_id":"A1"},
      "final_diagnoses":[{"status":"CONFIRMED","diagnosis_code":"DECLINE","confidence":0.86}],
      "treatment_recommendations":[{"target":"WRITER","treatment_code":"LIMITED","recommended_scope":["事実更新"]}],
      "referrals":[], "workflow":{}
    }
    r=CaseResultV2Builder().build(record)
    assert r["workflow"]["return_to"]=="SIMS_BLOG_MANAGER"
    assert r["workflow_handoff"]["handoff_mode"]=="RETURN_TO_SBM_FOR_REFERRAL"
    assert r["workflow_handoff"]["doctor_json_usage"]=="REQUIRED_SBM_REGISTRATION"
    assert r["workflow_handoff"]["writer_request_text"] is None
    assert r["compatibility"]["direct_specialist_invocation"]=="DISABLED"
