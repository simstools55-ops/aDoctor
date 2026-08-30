from __future__ import annotations

from collections import defaultdict
from math import log
import re
from typing import Any


class IntentDriftEngine:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.t = policy["thresholds"]

    def assess(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        observation = self._latest_search_observation(medical_record)
        if observation is None:
            return self._insufficient("Search Console観察データがありません。")

        facts = observation.get("facts", {})
        metrics = dict(facts.get("metrics", facts))
        impressions = float(metrics.get("impressions", 0))
        low_sample = bool(metrics.get("low_sample", False))
        queries = list(facts.get("queries", []))
        article = medical_record.get("patient", {})
        title = (
            article.get("article_title")
            or article.get("title")
            or facts.get("article_title")
            or ""
        )

        clusters = self._clusters(queries)
        total_impressions = sum(item["impressions"] for item in clusters.values())
        sorted_clusters = sorted(
            clusters.items(),
            key=lambda item: item[1]["impressions"],
            reverse=True,
        )
        primary = sorted_clusters[0] if sorted_clusters else None
        secondary = sorted_clusters[1] if len(sorted_clusters) > 1 else None
        primary_share = (
            primary[1]["impressions"] / total_impressions
            if primary and total_impressions > 0 else 0.0
        )
        secondary_share = (
            secondary[1]["impressions"] / total_impressions
            if secondary and total_impressions > 0 else 0.0
        )
        entropy = self._entropy([
            item[1]["impressions"] for item in sorted_clusters
        ])
        winner = self._winner_query(queries)
        overlap = self._query_title_overlap(
            primary[1]["queries"] if primary else [],
            title,
        )
        emerging = self._emerging_intent(facts)

        protections = {
            "winner_query_protected": bool(winner),
            "winner_query": winner,
            "new_article_allowed": False,
            "aggressive_retargeting_allowed": not bool(winner),
        }
        reasons = []

        if (
            low_sample
            or impressions < self.t["minimum_impressions"]
            or len(queries) < self.t["minimum_queries"]
        ):
            classification = "INSUFFICIENT_DATA"
            confidence = 45
            severity = "INFO"
            reasons.append("表示回数またはクエリ数が不足しています。")
        elif winner:
            classification = "WINNER_QUERY_PROTECTED"
            confidence = 88
            severity = "MILD"
            reasons.append("主要流入クエリを保護する必要があります。")
        elif emerging:
            classification = "EMERGING_INTENT_TRANSITION"
            confidence = 92
            severity = "MODERATE"
            reasons.append("新しい検索意図の流入が急増しています。")
        elif (
            primary_share < self.t["primary_intent_share_min"]
            and entropy >= self.t["intent_entropy_high"]
        ):
            classification = "TOPIC_DISPERSION"
            confidence = 90
            severity = "SEVERE"
            reasons.append("検索意図が複数方向へ分散しています。")
        elif (
            overlap < self.t["query_title_overlap_min"]
            and secondary_share >= self.t["secondary_intent_share_warning"]
        ):
            classification = "INTENT_DRIFT"
            confidence = 89
            severity = "SEVERE"
            reasons.append("主要流入クエリと記事タイトルの一致度が低下しています。")
        else:
            classification = "ALIGNED"
            confidence = 84
            severity = "INFO"
            reasons.append("主要検索意図と記事テーマは概ね一致しています。")

        if primary:
            reasons.append(
                f"最大クエリ群の表示構成比は{round(primary_share * 100, 1)}%です。"
            )
        if secondary:
            reasons.append(
                f"第2クエリ群の表示構成比は{round(secondary_share * 100, 1)}%です。"
            )
        reasons.append(
            f"クエリ分布エントロピーは{round(entropy, 3)}です。"
        )
        if title:
            reasons.append(
                f"主要クエリ群とタイトルの語彙一致度は{round(overlap * 100, 1)}%です。"
            )

        return {
            "classification": classification,
            "confidence": confidence,
            "severity": severity,
            "reasons": reasons,
            "metrics": {
                "impressions": impressions,
                "query_count": len(queries),
                "primary_intent": primary[0] if primary else None,
                "primary_intent_share": round(primary_share, 4),
                "secondary_intent": secondary[0] if secondary else None,
                "secondary_intent_share": round(secondary_share, 4),
                "intent_entropy": round(entropy, 4),
                "query_title_overlap": round(overlap, 4),
                "emerging_intent": emerging,
                "low_sample": low_sample,
            },
            "protections": protections,
            "trace": {
                "search_observation_id": observation.get("observation_id"),
                "finding_ids": [
                    item["finding_id"]
                    for item in medical_record.get("findings", [])
                    if item.get("finding_id")
                ],
            },
        }

    def _clusters(self, queries):
        clusters = defaultdict(lambda: {"impressions": 0.0, "queries": []})
        for item in queries:
            query = str(item.get("query", "")).strip()
            if not query:
                continue
            intent = item.get("intent_cluster") or self._infer_cluster(query)
            impressions = float(item.get("impressions", 0))
            clusters[intent]["impressions"] += impressions
            clusters[intent]["queries"].append(query)
        return dict(clusters)

    @staticmethod
    def _infer_cluster(query):
        tokens = [token for token in re.split(r"\s+", query.lower()) if token]
        if not tokens:
            return "UNKNOWN"
        return " ".join(tokens[:2])

    def _winner_query(self, queries):
        total_clicks = sum(float(item.get("clicks", 0)) for item in queries)
        if total_clicks <= 0:
            return None
        winner = max(
            queries,
            key=lambda item: float(item.get("clicks", 0)),
            default=None,
        )
        if winner is None:
            return None
        share = float(winner.get("clicks", 0)) / total_clicks
        if share >= self.t["winner_query_click_share"]:
            return {
                "query": winner.get("query"),
                "click_share": round(share, 4),
                "clicks": float(winner.get("clicks", 0)),
            }
        return None

    def _emerging_intent(self, facts):
        history = list(facts.get("intent_history", []))
        if len(history) < 2:
            return None
        previous = history[-2].get("shares", {})
        current = history[-1].get("shares", {})
        candidates = []
        for intent, current_share in current.items():
            previous_share = float(previous.get(intent, 0))
            current_share = float(current_share)
            growth = (
                (current_share - previous_share) / previous_share
                if previous_share > 0 else current_share
            )
            if growth >= self.t["emerging_intent_growth_ratio"]:
                candidates.append((growth, intent, previous_share, current_share))
        if not candidates:
            return None
        growth, intent, previous_share, current_share = max(candidates)
        return {
            "intent": intent,
            "growth_ratio": round(growth, 4),
            "previous_share": round(previous_share, 4),
            "current_share": round(current_share, 4),
        }

    @staticmethod
    def _entropy(values):
        total = sum(values)
        if total <= 0 or len(values) <= 1:
            return 0.0
        probabilities = [value / total for value in values if value > 0]
        raw = -sum(p * log(p) for p in probabilities)
        return raw / log(len(probabilities)) if len(probabilities) > 1 else 0.0

    @staticmethod
    def _query_title_overlap(queries, title):
        query_tokens = {
            token
            for query in queries
            for token in re.split(r"[\s　・｜|／/、,。！？!?（）()【】\[\]]+", query.lower())
            if token
        }
        title_tokens = {
            token
            for token in re.split(r"[\s　・｜|／/、,。！？!?（）()【】\[\]]+", title.lower())
            if token
        }
        if not query_tokens:
            return 0.0
        return len(query_tokens & title_tokens) / len(query_tokens)

    @staticmethod
    def _latest_search_observation(medical_record):
        items = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") in {
                "SEARCH_CONSOLE",
                "CURRENT_PERFORMANCE",
                "SINGLE_CASE_REQUEST",
            }
        ]
        return items[-1] if items else None

    @staticmethod
    def _insufficient(reason):
        return {
            "classification": "INSUFFICIENT_DATA",
            "confidence": 35,
            "severity": "INFO",
            "reasons": [reason],
            "metrics": {
                "impressions": 0.0,
                "query_count": 0,
                "primary_intent": None,
                "primary_intent_share": 0.0,
                "secondary_intent": None,
                "secondary_intent_share": 0.0,
                "intent_entropy": 0.0,
                "query_title_overlap": 0.0,
                "emerging_intent": None,
                "low_sample": True,
            },
            "protections": {
                "winner_query_protected": False,
                "winner_query": None,
                "new_article_allowed": False,
                "aggressive_retargeting_allowed": False,
            },
            "trace": {
                "search_observation_id": None,
                "finding_ids": [],
            },
        }
