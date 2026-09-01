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

def test_hard_serp_requires_cluster_check_before_close():
    r=diagnose_low_sample_serp(low_sample=True,target_query_confidence="MEDIUM",serp_checked=True,hard_serp=True)
    assert r["outcome"] == "CLUSTER_OPPORTUNITY_CHECK"

def test_creator_cluster_route():
    r=diagnose_low_sample_serp(low_sample=True,target_query_confidence="MEDIUM",serp_checked=True,hard_serp=True,cluster_checked=True,creator_opportunity=True)
    assert r["cluster_strategy_assessment"]["outcome"] == "CREATOR_OPPORTUNITY"
    assert r["cluster_strategy_assessment"]["route"] == "RETURN_TO_SBM_FOR_ACREATOR_REFERRAL"

def test_hard_serp_closes_only_after_no_cluster_opportunity():
    r=diagnose_low_sample_serp(low_sample=True,target_query_confidence="MEDIUM",serp_checked=True,hard_serp=True,cluster_checked=True)
    assert r["outcome"] == "LOW_PRIORITY_SERP_STRUCTURE"
