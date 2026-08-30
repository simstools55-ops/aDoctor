from doctor.output.case_result_v2 import CaseResultV2Builder


def test_writer_next_action():
    record = {
        "case_id": "C1",
        "patient": {"article_id": "A1"},
        "final_diagnoses": [{"status": "CONFIRMED", "diagnosis_code": "FRESHNESS"}],
        "treatment_recommendations": [{"target": "WRITER", "treatment_code": "LIMITED", "recommended_scope": ["更新"]}],
        "workflow": {},
    }
    result = CaseResultV2Builder().build(record)
    assert result["workflow_handoff"]["next_action"] == "WRITER"
