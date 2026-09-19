from __future__ import annotations

from typing import Any, Dict, Optional


def request_event(request: Dict[str, Any], request_id: str, received_at: str) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "requested_at": request["requested_at"],
        "received_at": received_at,
        "request_source": request["request_source"],
        "request_type": request["request_type"],
    }


def create_medical_record(
    request: Dict[str, Any],
    request_id: str,
    case_id: str,
    medical_record_id: str,
    received_at: str,
    previous_case: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    site = request["site"]
    article = request["article"]
    return {
        "contract_name": "SIMS_DOCTOR_MEDICAL_RECORD_V1",
        "contract_version": "1.0",
        "medical_record_id": medical_record_id,
        "case_id": case_id,
        "case_status": "READY_FOR_OBSERVATION",
        "personal_knowledge_site_id": request.get("personal_knowledge_site_id") or site.get("personal_knowledge_site_id"),
        "patient": {
            "site_id": site["site_id"],
            "site_name": site["site_name"],
            "blog_url": site["blog_url"],
            "personal_knowledge_site_id": site.get("personal_knowledge_site_id"),
            "article_id": article["article_id"],
            "article_url": article["url"],
            "article_title": article["title"],
        },
        "requests": [request_event(request, request_id, received_at)],
        "observations": [],
        "diagnoses": [],
        "referrals": [],
        "follow_ups": [],
        "counters": {
            "request_count": 1,
            "observation_count": 0,
            "diagnosis_count": 0,
            "referral_count": 0,
            "follow_up_count": 0,
        },
        "previous_case": previous_case,
        "created_at": received_at,
        "updated_at": received_at,
    }


def append_request(
    record: Dict[str, Any], request: Dict[str, Any], request_id: str, received_at: str
) -> Dict[str, Any]:
    updated = dict(record)
    updated["requests"] = list(record["requests"]) + [request_event(request, request_id, received_at)]
    updated["counters"] = dict(record["counters"])
    updated["counters"]["request_count"] += 1
    updated["updated_at"] = received_at
    return updated
