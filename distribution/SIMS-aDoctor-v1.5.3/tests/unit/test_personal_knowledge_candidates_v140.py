from doctor.output import CaseResultV2Builder


def _record():
    return {
        "case_id":"CASE-1", "medical_record_id":"MR-1",
        "personal_knowledge_site_id":"SITE-UUID-1",
        "patient":{"site_id":"infohack","article_id":"A000060","personal_knowledge_site_id":"SITE-UUID-1"},
        "final_diagnoses":[{"diagnosis_id":"D1","status":"CONFIRMED","diagnosis_code":"CONTENT_STALE","confidence":0.85,
            "knowledge_candidates":[{"scope":"SITE","knowledge_type":"CONTENT_FRESHNESS_RISK","statement":"A000060は外部サービス仕様変更による鮮度劣化リスクが高い記事である。","confidence":0.85,"evidence_refs":["A000060"]}]}],
        "treatment_recommendations":[], "referrals":[]
    }

def test_emits_optional_personal_knowledge_candidate_with_site_binding():
    r=CaseResultV2Builder().build(_record())
    c=r["knowledge_candidates"][0]
    assert r["personal_knowledge_site_id"]=="SITE-UUID-1"
    assert c["site_id"]=="SITE-UUID-1"
    assert c["confirmation_event_id"]=="CASE-1"
    assert c["source_product"]=="SIMS Article Doctor"

def test_does_not_invent_candidate_when_none_proposed():
    rec=_record(); rec["final_diagnoses"][0].pop("knowledge_candidates")
    r=CaseResultV2Builder().build(rec)
    assert r["knowledge_candidates"]==[]
