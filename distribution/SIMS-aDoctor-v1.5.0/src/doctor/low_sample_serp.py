from __future__ import annotations

VALID_OUTCOMES = {
    "SERP_GAP_ACTIONABLE", "SERP_COMPETITIVENESS_SUFFICIENT",
    "TARGET_QUERY_REASSESSMENT", "LOW_DEMAND_MAINTAIN",
    "ADDITIONAL_OBSERVATION", "LOW_PRIORITY_SERP_STRUCTURE",
}

def diagnose_low_sample_serp(*, low_sample: bool, target_query_confidence: str, serp_checked: bool, actionable_gap: bool=False, competitiveness_sufficient: bool=False, demand_low: bool=False, hard_serp: bool=False) -> dict:
    """Classify the fallback path used only when GSC evidence is insufficient."""
    if not low_sample:
        return {"activated": False, "outcome": None}
    confidence=str(target_query_confidence or "UNCONFIRMED").upper()
    if confidence == "UNCONFIRMED":
        return {"activated": True, "outcome": "TARGET_QUERY_REASSESSMENT"}
    if not serp_checked:
        return {"activated": True, "outcome": "ADDITIONAL_OBSERVATION"}
    if hard_serp and not actionable_gap:
        return {"activated": True, "outcome": "LOW_PRIORITY_SERP_STRUCTURE"}
    if actionable_gap:
        return {"activated": True, "outcome": "SERP_GAP_ACTIONABLE"}
    if competitiveness_sufficient and demand_low:
        return {"activated": True, "outcome": "LOW_DEMAND_MAINTAIN"}
    if competitiveness_sufficient:
        return {"activated": True, "outcome": "SERP_COMPETITIVENESS_SUFFICIENT"}
    return {"activated": True, "outcome": "ADDITIONAL_OBSERVATION"}
