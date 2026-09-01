from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


SBM_V2_FORMAT = "SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2"


def is_sbm_v2(payload: Mapping[str, Any]) -> bool:
    return payload.get("format") == SBM_V2_FORMAT


def adapt_sbm_v2(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Adapt the SBM Evidence Package V2 request to the legacy Doctor intake model.

    The raw V2 request remains available to callers for audit. This adapter only
    creates the normalized intake representation used by the existing clinical
    pipeline. Case ownership remains with SBM when ``case_id`` is supplied.
    """
    root = deepcopy(dict(payload))
    request = root.get("request") or {}
    site = root.get("site") or {}
    article = root.get("article") or {}
    workflow = root.get("workflow") or {}
    case_id = root.get("case_id") or request.get("case_id")
    requested_at = request.get("requested_at") or root.get("generated_at")
    source_sheet = request.get("source_sheet") or "記事管理"
    source_screen = "IMPROVEMENT_TREND" if "改善" in str(source_sheet) else "ARTICLE_LIST"

    adapted = {
        "contract_name": "SIMS_DOCTOR_SINGLE_CASE_REQUEST_V1",
        "contract_version": "1.0",
        "requested_at": requested_at,
        "request_source": "SIMS_BLOG_MANAGER",
        "request_type": "SINGLE_CASE_DIAGNOSIS",
        "site": {
            "site_id": site.get("site_id"),
            "site_name": site.get("site_name"),
            "blog_url": site.get("blog_url"),
            "personal_knowledge_site_id": site.get("personal_knowledge_site_id"),
        },
        "article": {
            "article_id": article.get("article_id"),
            "url": article.get("url") or article.get("canonical_url"),
            "title": article.get("title") or article.get("h1"),
        },
        "trigger": {
            "source_screen": source_screen,
            "reason": request.get("chief_complaint") or request.get("trigger") or "SBMからの個別診断依頼",
        },
        "case_id": case_id,
        "sbm_request_id": request.get("request_id"),
        "personal_knowledge_site_id": site.get("personal_knowledge_site_id"),
        "workflow": workflow,
        "evidence_package": root.get("evidence_package"),
        "source_contract": {
            "format": root.get("format"),
            "contract_version": root.get("contract_version"),
            "schema_version": root.get("schema_version"),
            "message_id": root.get("message_id"),
        },
    }
    return adapted
