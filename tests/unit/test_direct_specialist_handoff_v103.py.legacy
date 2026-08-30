from src.doctor.output.case_result_v2 import CaseResultV2Builder

def test_direct_writer_handoff_and_optional_doctor_archive():
    record={
      "case_id":"CASE-1", "patient":{"site_id":"S","article_id":"A"},
      "final_diagnoses":[{"diagnosis_id":"D","status":"CONFIRMED","diagnosis_code":"X"}],
      "treatment_recommendations":[{"target":"WRITER","recommended_scope":["内部リンク追加"]}]
    }
    r=CaseResultV2Builder().build(record)
    assert r["workflow"]["return_to"]=="DIRECT_SPECIALIST_HANDOFF"
    assert r["workflow_handoff"]["handoff_mode"]=="DIRECT_TO_SPECIALIST"
    assert r["workflow_handoff"]["doctor_json_usage"]=="OPTIONAL_ARCHIVE_ONLY"
    assert "処置後の結果はSBMへ登録" in r["workflow_handoff"]["writer_request_text"]
