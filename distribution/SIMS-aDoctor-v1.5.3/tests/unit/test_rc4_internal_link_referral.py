from doctor.output.case_result_v2 import CaseResultV2Builder


def _record():
    return {
        "case_id": "CASE-RC4",
        "medical_record_id": "MR-RC4",
        "patient": {"site_id": "s", "article_id": "a"},
        "final_diagnoses": [{"status":"CONFIRMED","diagnosis_code":"POSITION_OPPORTUNITY","summary":"x"}],
        "treatment_recommendations": [{
            "target":"WRITER",
            "treatment_level":"LIMITED",
            "recommended_scope":["INTERNAL_LINK_ADDITION_MAX_2"],
            "prohibited_actions":["FULL_REWRITE","TITLE_CHANGE"],
            "internal_link_recommendations":[{
                "url":"https://example.com/819",
                "title":"Keyboard position fix",
                "reason":"same keyboard trouble cluster",
                "relationship":"adjacent symptom",
                "suggested_context":"after troubleshooting section",
                "anchor":"keyboard position trouble"
            }]
        }],
        "referrals":[{"target":"WRITER"}],
    }


def test_rc4_internal_link_metadata_reaches_all_referral_layers():
    r=CaseResultV2Builder().build(_record())
    rec=r["treatment_plan"]["internal_link_recommendations"][0]
    assert rec["url"].endswith("/819")
    assert rec["reason"] == "same keyboard trouble cluster"
    assert rec["writer_must_finalize_anchor"] is True
    assert r["referral"]["internal_link_recommendations"] == r["workflow_handoff"]["internal_link_recommendations"]
    assert r["workflow_handoff"]["allowed_scope"] == ["INTERNAL_LINK_ADDITION_MAX_2"]
    assert "FULL_REWRITE" in r["workflow_handoff"]["blocked_scope"]
