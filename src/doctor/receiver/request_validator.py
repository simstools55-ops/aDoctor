from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from urllib.parse import urlparse

from doctor.common.errors import (
    DoctorError, INVALID_DATETIME, INVALID_FIELD_TYPE, INVALID_FIELD_VALUE,
    INVALID_URL, MISSING_REQUIRED_FIELD, UNSUPPORTED_CONTRACT,
    UNSUPPORTED_VERSION,
)

CONTRACT_NAME = "SIMS_DOCTOR_SINGLE_CASE_REQUEST_V1"
CONTRACT_VERSION = "1.0"
REQUEST_SOURCE = "SIMS_BLOG_MANAGER"
REQUEST_TYPE = "SINGLE_CASE_DIAGNOSIS"
SOURCE_SCREENS = {"ARTICLE_LIST", "IMPROVEMENT_TREND"}


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DoctorError(INVALID_FIELD_TYPE, f"{field} must be an object", field)
    return value


def _require_string(value: Any, field: str, max_length: int) -> str:
    if value is None:
        raise DoctorError(MISSING_REQUIRED_FIELD, f"{field} is required", field)
    if not isinstance(value, str):
        raise DoctorError(INVALID_FIELD_TYPE, f"{field} must be a string", field)
    normalized = value.strip()
    if not normalized:
        raise DoctorError(MISSING_REQUIRED_FIELD, f"{field} is required", field)
    if len(normalized) > max_length:
        raise DoctorError(INVALID_FIELD_VALUE, f"{field} is too long", field)
    return normalized


def _validate_http_url(value: Any, field: str) -> str:
    url = _require_string(value, field, 2048)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise DoctorError(INVALID_URL, f"{field} must be an absolute HTTP(S) URL", field)
    return url


def _validate_datetime(value: Any, field: str) -> str:
    text = _require_string(value, field, 100)
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise DoctorError(INVALID_DATETIME, f"{field} must be ISO 8601", field) from exc
    if parsed.tzinfo is None:
        raise DoctorError(INVALID_DATETIME, f"{field} must include a timezone", field)
    return text


def validate_request(payload: Any) -> None:
    root = _require_mapping(payload, "request")

    contract_name = _require_string(root.get("contract_name"), "contract_name", 100)
    if contract_name != CONTRACT_NAME:
        raise DoctorError(UNSUPPORTED_CONTRACT, "unsupported contract_name", "contract_name")

    contract_version = _require_string(root.get("contract_version"), "contract_version", 20)
    if contract_version != CONTRACT_VERSION:
        raise DoctorError(UNSUPPORTED_VERSION, "unsupported contract_version", "contract_version")

    _validate_datetime(root.get("requested_at"), "requested_at")

    source = _require_string(root.get("request_source"), "request_source", 100)
    if source != REQUEST_SOURCE:
        raise DoctorError(INVALID_FIELD_VALUE, "unsupported request_source", "request_source")

    request_type = _require_string(root.get("request_type"), "request_type", 100)
    if request_type != REQUEST_TYPE:
        raise DoctorError(INVALID_FIELD_VALUE, "unsupported request_type", "request_type")

    site = _require_mapping(root.get("site"), "site")
    _require_string(site.get("site_id"), "site.site_id", 100)
    _require_string(site.get("site_name"), "site.site_name", 300)
    _validate_http_url(site.get("blog_url"), "site.blog_url")

    article = _require_mapping(root.get("article"), "article")
    _require_string(article.get("article_id"), "article.article_id", 100)
    _validate_http_url(article.get("url"), "article.url")
    _require_string(article.get("title"), "article.title", 1000)

    trigger = _require_mapping(root.get("trigger"), "trigger")
    screen = _require_string(trigger.get("source_screen"), "trigger.source_screen", 100)
    if screen not in SOURCE_SCREENS:
        raise DoctorError(INVALID_FIELD_VALUE, "unsupported source_screen", "trigger.source_screen")
    _require_string(trigger.get("reason"), "trigger.reason", 200)
