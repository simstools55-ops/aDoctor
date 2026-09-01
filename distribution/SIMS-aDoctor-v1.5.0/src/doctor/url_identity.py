"""URL identity and canonicalization support for diagnostic triage.

This module does not make network requests. It normalizes evidence supplied by
SBM, Search Console, a CMS, or a manual check so Doctor does not mistake a
trailing-slash alias for an indexing failure.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urlsplit, urlunsplit


def _normalize(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    parts = urlsplit(value)
    scheme = parts.scheme.lower()
    host = parts.netloc.lower()
    path = parts.path or "/"
    # Query and fragment do not define the article identity for this check.
    return urlunsplit((scheme, host, path, "", ""))


def trailing_slash_variant(url: str) -> str:
    normalized = _normalize(url)
    if not normalized:
        return ""
    parts = urlsplit(normalized)
    path = parts.path
    if path == "/":
        return normalized
    path = path[:-1] if path.endswith("/") else path + "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def same_resource_by_trailing_slash(left: str, right: str) -> bool:
    a, b = _normalize(left), _normalize(right)
    if not a or not b:
        return False
    if a == b:
        return True
    return trailing_slash_variant(a) == b


@dataclass(frozen=True)
class UrlIdentityAssessment:
    requested_url: str
    matched_url: str
    canonical_url: str
    google_selected_canonical: str
    redirect_target: str
    same_resource: bool
    status: str
    diagnosis_note_ja: str
    requires_user_action: bool

    def to_dict(self) -> dict:
        return asdict(self)


def assess_url_identity(
    requested_url: str,
    *,
    matched_url: str = "",
    canonical_url: str = "",
    google_selected_canonical: str = "",
    redirect_target: str = "",
    indexed_requested: Optional[bool] = None,
    indexed_matched: Optional[bool] = None,
) -> UrlIdentityAssessment:
    """Classify URL evidence without over-diagnosing trailing-slash differences.

    Status values:
    - SAME_RESOURCE_NORMALIZATION: slash/no-slash aliases resolve to one resource.
    - INDEXED_CANONICAL_CONFIRMED: canonical URL is indexed; ranking loss is not an indexing loss.
    - TECHNICAL_INDEX_RISK: supplied evidence points to a real technical indexing problem.
    - INSUFFICIENT_URL_EVIDENCE: no reliable conclusion is possible.
    """
    req = _normalize(requested_url)
    matched = _normalize(matched_url)
    canonical = _normalize(canonical_url)
    google = _normalize(google_selected_canonical)
    redirect = _normalize(redirect_target)
    candidates = [u for u in (matched, canonical, google, redirect) if u]
    same = any(same_resource_by_trailing_slash(req, u) for u in candidates)

    canonical_indexed = indexed_matched is True and bool(matched)
    if canonical_indexed and same:
        return UrlIdentityAssessment(
            req, matched, canonical, google, redirect, True,
            "INDEXED_CANONICAL_CONFIRMED",
            "末尾スラッシュの表記差はありますが、正規URLはインデックスされています。インデックス消失ではなく、検索評価低下など別要因を優先して診断します。",
            False,
        )
    if same:
        return UrlIdentityAssessment(
            req, matched, canonical, google, redirect, True,
            "SAME_RESOURCE_NORMALIZATION",
            "末尾スラッシュの有無は同一ページのURL正規化として扱います。この差だけでインデックス異常とは判断しません。",
            False,
        )
    if indexed_requested is False and indexed_matched is False:
        return UrlIdentityAssessment(
            req, matched, canonical, google, redirect, False,
            "TECHNICAL_INDEX_RISK",
            "確認できた候補URLがいずれも未登録です。noindex、canonical、robots、404やリダイレクトを技術確認してください。",
            True,
        )
    return UrlIdentityAssessment(
        req, matched, canonical, google, redirect, False,
        "INSUFFICIENT_URL_EVIDENCE",
        "URLの正規化情報が不足しています。大規模リライトは保留し、Googleが選択した正規URLだけ追加確認してください。",
        True,
    )
