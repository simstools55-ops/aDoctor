from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


class CrossArticleAnalyzer:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.thresholds = policy["thresholds"]

    def analyze(
        self,
        *,
        primary_article: dict[str, Any],
        candidate_articles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        output = []
        primary_queries = self._query_map(primary_article)
        for candidate in candidate_articles:
            candidate_queries = self._query_map(candidate)
            shared = sorted(set(primary_queries) & set(candidate_queries))
            union = set(primary_queries) | set(candidate_queries)
            overlap = len(shared) / len(union) if union else 0.0
            title_similarity = SequenceMatcher(
                None,
                primary_article["title"].lower(),
                candidate["title"].lower(),
            ).ratio()
            intent_similarity = float(candidate.get("intent_similarity", 0.0))

            shared_rows = [
                {
                    "query": query,
                    "primary_impressions": primary_queries[query],
                    "candidate_impressions": candidate_queries[query],
                }
                for query in shared
            ]
            classification, dominant = self._classify(
                primary_article, candidate, shared, overlap,
                title_similarity, intent_similarity
            )
            output.append({
                "article": {
                    key: candidate[key]
                    for key in (
                        "article_id", "url", "title", "main_query",
                        "clicks", "impressions", "ctr", "position"
                    )
                },
                "shared_queries": shared_rows,
                "query_overlap_ratio": round(overlap, 4),
                "title_similarity": round(title_similarity, 4),
                "intent_similarity": round(intent_similarity, 4),
                "classification": classification,
                "dominant_article_id": dominant,
            })
        return output

    def _classify(
        self, primary, candidate, shared, overlap, title_similarity, intent_similarity
    ):
        t = self.thresholds
        candidate_impressions = candidate.get("impressions", 0)
        if candidate_impressions < t["minimum_candidate_impressions"]:
            return "NO_CONFLICT", None

        if (
            len(shared) >= t["minimum_shared_queries"]
            and overlap >= t["minimum_query_overlap_ratio"]
            and intent_similarity >= t["minimum_intent_similarity"]
        ):
            dominant = self._dominant(primary, candidate)
            if title_similarity >= t["minimum_title_similarity"]:
                return "MERGE_CANDIDATE", dominant
            return "POSSIBLE_CANNIBALIZATION", dominant

        if intent_similarity < t["minimum_intent_similarity"] and shared:
            return "SEPARATE_INTENT", None

        if not shared and intent_similarity < 0.5:
            return "NEW_ARTICLE_OPPORTUNITY", None

        return "NO_CONFLICT", None

    def _dominant(self, primary, candidate):
        p = max(primary.get("clicks", 0), 1)
        c = max(candidate.get("clicks", 0), 1)
        ratio = self.thresholds["dominance_ratio_for_primary_article"]
        if p / c >= ratio:
            return primary["article_id"]
        if c / p >= ratio:
            return candidate["article_id"]
        return None

    @staticmethod
    def _query_map(article):
        return {
            item["query"]: float(item.get("impressions", 0))
            for item in article.get("queries", [])
            if item.get("query")
        }
