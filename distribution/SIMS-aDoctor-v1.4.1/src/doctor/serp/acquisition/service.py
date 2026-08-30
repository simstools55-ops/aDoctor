from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
import time
from typing import Any, Callable

from .provider import SerpProvider, SerpProviderError


class SerpAcquisitionService:
    def __init__(
        self,
        provider: SerpProvider,
        policy: dict[str, Any],
        *,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.provider = provider
        self.policy = policy
        self.sleep = sleep

    def acquire(
        self,
        *,
        case_id: str,
        site_id: str,
        article_id: str,
        article_url: str,
        query: str,
        previous_observation: dict[str, Any] | None = None,
        requested_at: datetime | None = None,
    ) -> dict[str, Any]:
        requested = requested_at or datetime.now(timezone.utc)
        try:
            response = self._search_with_retry(query)
            status = "COMPLETE" if response.results else "NO_DATA"
            error_code = None
            error_message = None
        except SerpProviderError as exc:
            response = None
            status = "FAILED"
            error_code = exc.code
            error_message = exc.message

        completed = datetime.now(timezone.utc)
        results = list(response.results) if response else []
        intent = self._infer_intent(query, results)
        features = list(response.features) if response else []
        competition = self._competition(results, features)
        comparison = self._compare(previous_observation, intent, features, results)

        return {
            "contract_name": "SIMS_DOCTOR_SERP_OBSERVATION_INPUT_V1",
            "contract_version": "1.0",
            "case_id": case_id,
            "article": {
                "site_id": site_id,
                "article_id": article_id,
                "url": article_url,
            },
            "query": query,
            "retrieval": {
                "requested_at": requested.isoformat(),
                "completed_at": completed.isoformat(),
                "status": status,
                "error_code": error_code,
                "error_message": error_message,
            },
            "intent": intent,
            "features": features,
            "results": [
                {
                    "position": item.position,
                    "title": item.title,
                    "url": item.url,
                    "domain": item.domain,
                    "snippet": item.snippet[: self.policy["privacy"]["maximum_snippet_length"]],
                    "published_at": item.published_at,
                    "updated_at": item.updated_at,
                    "authority_score": item.authority_score,
                    "intent_match": item.intent_match,
                }
                for item in results[: self.policy["result_limit"]]
            ],
            "competition": competition,
            "comparison": comparison,
        }

    def _search_with_retry(self, query: str):
        retry = self.policy["retry"]
        retryable = set(retry["retryable_errors"])
        maximum = int(retry["maximum_attempts"])
        for attempt in range(1, maximum + 1):
            try:
                return self.provider.search(query, result_limit=self.policy["result_limit"])
            except SerpProviderError as exc:
                if exc.code not in retryable or attempt == maximum:
                    raise
                self.sleep(float(attempt))
        raise RuntimeError("Unreachable")

    @staticmethod
    def _infer_intent(query: str, results) -> dict[str, Any]:
        q = query.lower()
        signals = []
        if any(token in q for token in ("方法", "やり方", "設定", "how")):
            primary = "HOW_TO"
            signals.append("QUERY_HOW_TO_TOKEN")
        elif any(token in q for token in ("比較", "おすすめ", "違い", "vs")):
            primary = "COMPARISON"
            signals.append("QUERY_COMPARISON_TOKEN")
        elif any(token in q for token in ("購入", "価格", "料金", "申込")):
            primary = "TRANSACTIONAL"
            signals.append("QUERY_TRANSACTION_TOKEN")
        elif any(token in q for token in ("ログイン", "公式", "サイト")):
            primary = "NAVIGATIONAL"
            signals.append("QUERY_NAVIGATIONAL_TOKEN")
        else:
            primary = "INFORMATIONAL"
            signals.append("DEFAULT_INFORMATIONAL")

        title_text = " ".join(item.title.lower() for item in results[:5])
        if primary == "INFORMATIONAL" and any(token in title_text for token in ("方法", "手順", "how")):
            primary = "HOW_TO"
            signals.append("SERP_HOW_TO_TITLES")

        confidence = min(95, 60 + 10 * len(signals))
        return {"primary": primary, "confidence": confidence, "signals": signals}

    def _competition(self, results, features: list[str]) -> dict[str, int]:
        if not results:
            return {
                "strength_score": 0,
                "freshness_score": 0,
                "intent_match_score": 0,
                "feature_pressure_score": 0,
            }

        authority = [item.authority_score for item in results if item.authority_score is not None]
        intent = [item.intent_match for item in results if item.intent_match is not None]
        freshness_count = sum(1 for item in results if item.updated_at or item.published_at)

        authority_score = round(mean(authority)) if authority else 50
        intent_score = round(mean(intent)) if intent else 50
        freshness_score = round(100 * freshness_count / len(results))
        feature_pressure = min(100, len(features) * 15)

        weights = self.policy["competition"]
        strength = round(
            authority_score * weights["authority_weight"]
            + intent_score * weights["exact_intent_match_weight"]
            + freshness_score * weights["freshness_weight"]
            + feature_pressure * weights["serp_feature_weight"]
        )
        return {
            "strength_score": max(0, min(100, strength)),
            "freshness_score": freshness_score,
            "intent_match_score": intent_score,
            "feature_pressure_score": feature_pressure,
        }

    @staticmethod
    def _compare(previous, intent, features, results):
        if previous is None:
            return None
        prev_facts = previous.get("facts", {})
        prev_domains = {item["domain"] for item in prev_facts.get("results", [])}
        current_domains = {item.domain for item in results}
        prev_features = set(prev_facts.get("features", []))
        current_features = set(features)
        previous_intent = prev_facts.get("intent", {}).get("primary")
        return {
            "previous_observation_id": previous.get("observation_id"),
            "new_domains": sorted(current_domains - prev_domains),
            "lost_domains": sorted(prev_domains - current_domains),
            "intent_changed": previous_intent is not None and previous_intent != intent["primary"],
            "feature_changes": sorted(prev_features.symmetric_difference(current_features)),
        }
