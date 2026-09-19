from doctor.output.case_result_v2 import CaseResultV2Builder


def _record():
    return {
        "case_id": "CASE-RC3",
        "patient": {"site_id": "SITE", "article_id": "A1"},
        "final_diagnoses": [{
            "status": "CONFIRMED",
            "diagnosis_code": "LONG_TERM_DECAY",
            "summary": "記事本文に重大な問題はなく、限定的な修正で経過を確認します。",
        }],
        "treatment_recommendations": [{
            "target": "WRITER",
            "treatment_code": "LIMITED",
            "strategy": "LIGHT_FIX",
            "recommended_scope": ["内部リンク追加"],
            "prohibited_actions": ["FULL_REWRITE", "AUTOMATIC_DELETE", "NEW_ARTICLE_CREATION"],
            "monitoring": {"recommended_review_days": 28},
            "strategy_reason": "大規模変更より限定修正を優先します。",
        }],
        "workflow": {},
    }


def test_rc3_presentation_has_human_blocks():
    result = CaseResultV2Builder().build(_record())
    p = result["presentation"]
    assert p["standard"] == "SIMS_PRESENTATION_STANDARD_V1"
    assert p["summary"]
    assert p["do_now"]
    assert p["do_not"]
    assert p["next_step"]


def test_rc3_presentation_hides_machine_field_names():
    result = CaseResultV2Builder().build(_record())
    blob = str(result["presentation"]).lower()
    for token in ["allowed_scope", "blocked_scope", "handoff_mode", "contract", "schema"]:
        assert token not in blob


def test_rc3_referral_contract_remains_machine_facing():
    result = CaseResultV2Builder().build(_record())
    assert result["referral"]["allowed_scope"] == ["内部リンク追加"]
    assert "FULL_REWRITE" in result["referral"]["blocked_scope"]
    assert result["workflow_handoff"]["handoff_mode"] == "RETURN_TO_SBM_FOR_REFERRAL"


def test_rc3_wait_presentation_is_actionable():
    record = _record()
    record["treatment_recommendations"][0].update({
        "target": "OBSERVE",
        "strategy": "WAIT",
        "recommended_scope": ["MONITORING"],
        "user_todo": [{"instruction": "記事を大きく変更せず、14日後に再診してください。"}],
        "monitoring": {"recommended_review_days": 14},
    })
    result = CaseResultV2Builder().build(record)
    p = result["presentation"]
    assert any("14日後" in x for x in p["do_now"])
    assert any("全面リライト" in x for x in p["do_not"])
    assert "14日後" in p["next_step"]
