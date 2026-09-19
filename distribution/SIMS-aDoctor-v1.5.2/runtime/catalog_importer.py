"""SIMS Doctor article catalog importer v0.1.0."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
import uuid

SUPPORTED_FORMAT = "SIMS_DOCTOR_ARTICLE_CATALOG_V1"
SUPPORTED_CONTRACT = "1.0"

class CatalogValidationError(ValueError):
    pass

@dataclass(frozen=True)
class CollectorJob:
    job_id: str
    site_id: str
    catalog_id: str
    status: str
    job_type: str
    created_at: str

def validate_catalog(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise CatalogValidationError("payload must be an object")
    if payload.get("format") != SUPPORTED_FORMAT:
        raise CatalogValidationError("unsupported format")
    if payload.get("contract_version") != SUPPORTED_CONTRACT:
        raise CatalogValidationError("unsupported contract_version")
    site = payload.get("site") or {}
    if not site.get("site_id"):
        raise CatalogValidationError("site.site_id is required")
    catalog = payload.get("catalog") or {}
    if not catalog.get("catalog_id"):
        raise CatalogValidationError("catalog.catalog_id is required")
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise CatalogValidationError("articles must be an array")
    seen=set()
    for i, article in enumerate(articles):
        aid=str((article or {}).get("article_id") or "").strip()
        url=str((article or {}).get("url") or "").strip()
        if not aid: raise CatalogValidationError(f"articles[{i}].article_id is required")
        if not url: raise CatalogValidationError(f"articles[{i}].url is required")
        if aid in seen: raise CatalogValidationError(f"duplicate article_id: {aid}")
        seen.add(aid)
    if catalog.get("article_count") != len(articles):
        raise CatalogValidationError("catalog.article_count mismatch")

def create_collector_job(payload: Dict[str, Any]) -> CollectorJob:
    validate_catalog(payload)
    now=datetime.now(timezone.utc).isoformat()
    return CollectorJob(
        job_id="JOB-" + uuid.uuid4().hex[:16].upper(),
        site_id=payload["site"]["site_id"],
        catalog_id=payload["catalog"]["catalog_id"],
        status="READY",
        job_type="INITIAL_SCREENING",
        created_at=now,
    )
