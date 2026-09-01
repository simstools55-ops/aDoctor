from src.doctor.low_sample_serp import diagnose_low_sample_serp

def test_low_sample_actionable_gap():
    r=diagnose_low_sample_serp(low_sample=True,target_query_confidence="LOW",serp_checked=True,actionable_gap=True)
    assert r["outcome"] == "SERP_GAP_ACTIONABLE"

def test_low_demand_normal_close():
    r=diagnose_low_sample_serp(low_sample=True,target_query_confidence="MEDIUM",serp_checked=True,competitiveness_sufficient=True,demand_low=True)
    assert r["outcome"] == "LOW_DEMAND_MAINTAIN"

def test_unconfirmed_query_reassessment():
    r=diagnose_low_sample_serp(low_sample=True,target_query_confidence="UNCONFIRMED",serp_checked=True)
    assert r["outcome"] == "TARGET_QUERY_REASSESSMENT"
