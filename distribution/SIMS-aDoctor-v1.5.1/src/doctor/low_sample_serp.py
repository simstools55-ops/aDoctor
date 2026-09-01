from __future__ import annotations

VALID_OUTCOMES = {
    "SERP_GAP_ACTIONABLE", "SERP_COMPETITIVENESS_SUFFICIENT",
    "TARGET_QUERY_REASSESSMENT", "LOW_DEMAND_MAINTAIN",
    "ADDITIONAL_OBSERVATION", "CLUSTER_OPPORTUNITY_CHECK",
    "LOW_PRIORITY_SERP_STRUCTURE",
}

VALID_CLUSTER_OUTCOMES = {
    "EXISTING_CONTENT_SUPPORT", "CREATOR_OPPORTUNITY", "NO_CLUSTER_OPPORTUNITY",
}

def diagnose_cluster_opportunity(*, cluster_checked: bool, existing_content_support: bool=False, creator_opportunity: bool=False) -> dict:
    if not cluster_checked:
        return {"checked": False, "outcome": None, "route": "CLUSTER_OPPORTUNITY_CHECK"}
    if existing_content_support:
        return {"checked": True, "outcome": "EXISTING_CONTENT_SUPPORT", "route": "RETURN_TO_SBM_FOR_AWRITER_SUPPORT"}
    if creator_opportunity:
        return {"checked": True, "outcome": "CREATOR_OPPORTUNITY", "route": "RETURN_TO_SBM_FOR_ACREATOR_REFERRAL"}
    return {"checked": True, "outcome": "NO_CLUSTER_OPPORTUNITY", "route": "RETURN_TO_SBM_AS_NORMAL_CLOSE"}

def diagnose_low_sample_serp(*, low_sample: bool, target_query_confidence: str, serp_checked: bool, actionable_gap: bool=False, competitiveness_sufficient: bool=False, demand_low: bool=False, hard_serp: bool=False, cluster_checked: bool=False, existing_content_support: bool=False, creator_opportunity: bool=False) -> dict:
    """Classify LOW_SAMPLE using SERP first, then cluster strategy when the head SERP is structurally hard."""
    if not low_sample:
        return {"activated": False, "outcome": None}
    confidence=str(target_query_confidence or "UNCONFIRMED").upper()
    if confidence == "UNCONFIRMED":
        return {"activated": True, "outcome": "TARGET_QUERY_REASSESSMENT"}
    if not serp_checked:
        return {"activated": True, "outcome": "ADDITIONAL_OBSERVATION"}
    if actionable_gap:
        return {"activated": True, "outcome": "SERP_GAP_ACTIONABLE"}
    if hard_serp:
        cluster=diagnose_cluster_opportunity(cluster_checked=cluster_checked, existing_content_support=existing_content_support, creator_opportunity=creator_opportunity)
        if not cluster_checked:
            return {"activated": True, "outcome": "CLUSTER_OPPORTUNITY_CHECK", "cluster_strategy_assessment": cluster}
        if cluster["outcome"] == "NO_CLUSTER_OPPORTUNITY":
            return {"activated": True, "outcome": "LOW_PRIORITY_SERP_STRUCTURE", "cluster_strategy_assessment": cluster}
        return {"activated": True, "outcome": "CLUSTER_OPPORTUNITY_CHECK", "cluster_strategy_assessment": cluster}
    if competitiveness_sufficient and demand_low:
        return {"activated": True, "outcome": "LOW_DEMAND_MAINTAIN"}
    if competitiveness_sufficient:
        return {"activated": True, "outcome": "SERP_COMPETITIVENESS_SUFFICIENT"}
    return {"activated": True, "outcome": "ADDITIONAL_OBSERVATION"}
