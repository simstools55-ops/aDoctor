from __future__ import annotations
from typing import Any, Mapping

FORMAT="SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2"

def validate_manager_v2_gate(payload: Mapping[str, Any]) -> tuple[bool, str]:
    if payload.get("format") != FORMAT: return False, "format"
    if str(payload.get("contract_version")) != "2.0": return False, "contract_version"
    if str(payload.get("schema_version")) != "2.0.0": return False, "schema_version"
    if payload.get("source_system") != "SIMS_BLOG_MANAGER": return False, "source_system"
    if payload.get("target_system") != "SIMS_DOCTOR": return False, "target_system"
    request=payload.get("request") or {}; site=payload.get("site") or {}; article=payload.get("article") or {}
    rid=request.get("request_id"); cid=payload.get("case_id") or request.get("case_id"); sid=site.get("site_id"); aid=article.get("article_id")
    for name,val in (("request_id",rid),("case_id",cid),("site_id",sid),("article_id",aid)):
        if val is None or not str(val).strip(): return False,name
    if payload.get("case_id") and request.get("case_id") and payload.get("case_id") != request.get("case_id"):
        return False,"case_id_mismatch"
    return True,"OK"
