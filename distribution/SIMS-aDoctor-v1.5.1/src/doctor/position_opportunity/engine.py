from __future__ import annotations

from typing import Any


class PositionOpportunityEngine:
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
        clicks = float(metrics.get("clicks", 0))
        ctr = float(metrics.get("ctr", 0))
        position = metrics.get("position")
        position = float(position) if position is not None else None
        low_sample = bool(metrics.get("low_sample", False))

        queries = list(facts.get("queries", []))
        winner = self._winner_query(queries)
        query_focus = self._query_focus(queries)
        competition_resilience = self._vital_sign_score(
            medical_record, "COMPETITION_RESILIENCE"
        )
        content_integrity = self._vital_sign_score(
            medical_record, "CONTENT_INTEGRITY"
        )

        protections = {
            "winner_query_protected": bool(winner),
            "winner_query": winner,
            "aggressive_rewrite_allowed": (
                content_integrity is None
                or content_integrity >= self.t["content_integrity_min"]
            ),
            "new_article_allowed": False,
        }
        reasons = []

        if (
            low_sample
            or impressions < self.t["minimum_impressions"]
            or position is None
        ):
            classification = "INSUFFICIENT_DATA"
            confidence = 45
            severity = "INFO"
            reasons.append("表示回数または順位データが不足しています。")
        elif winner:
            classification = "WINNER_QUERY_PROTECTED"
            confidence = 88
            severity = "MILD"
            reasons.append("主要流入クエリを保護する必要があります。")
        elif position <= self.t["near_page_one_min"]:
            classification = "HEALTHY_POSITION"
            confidence = 84
            severity = "INFO"
            reasons.append("現在順位は既に良好な範囲です。")
        elif (
            self.t["strong_opportunity_min"]
            <= position
            <= self.t["strong_opportunity_max"]
            and self._resilience_ok(competition_resilience)
        ):
            classification = "HIGH_POSITION_OPPORTUNITY"
            confidence = 94
            severity = "SEVERE"
            reasons.append("上位表示まであと一歩で、改善効果が期待できます。")
        elif (
            self.t["near_page_one_min"]
            < position
            <= self.t["near_page_one_max"]
        ):
            if query_focus:
                classification = "QUERY_FOCUSED_OPPORTUNITY"
                confidence = 90
                severity = "MODERATE"
                reasons.append("特定クエリ群への集中があり、見出し・回答強化余地があります。")
            else:
                classification = "POSITION_OPPORTUNITY"
                confidence = 86
                severity = "MODERATE"
                reasons.append("表示回数があり、1ページ目付近まで上昇する余地があります。")
        elif position >= self.t["weak_visibility_position"]:
            classification = "LOW_VISIBILITY_OR_MISALIGNMENT"
            confidence = 82
            severity = "SEVERE"
            reasons.append("順位が低く、検索意図または記事役割のずれが疑われます。")
        else:
            classification = "HEALTHY_POSITION"
            confidence = 76
            severity = "INFO"
            reasons.append("現時点では順位改善の優先度は高くありません。")

        if competition_resilience is not None:
            reasons.append(
                f"Competition Resilienceは{competition_resilience}点です。"
            )
        if content_integrity is not None and content_integrity < self.t["content_integrity_min"]:
            reasons.append(
                "Content Integrityが低いため、局所改善ではなく記事構造の再確認が必要です。"
            )
        if query_focus:
            reasons.append(
                f"上位クエリ群の表示集中率は{round(query_focus['impression_share'] * 100, 1)}%です。"
            )

        return {
            "classification": classification,
            "confidence": confidence,
            "severity": severity,
            "reasons": reasons,
            "metrics": {
                "clicks": clicks,
                "impressions": impressions,
                "ctr": round(ctr, 6),
                "position": position,
                "competition_resilience": competition_resilience,
                "content_integrity": content_integrity,
                "query_focus": query_focus,
                "low_sample": low_sample,
            },
            "protections": protections,
            "trace": {
                "search_observation_id": observation.get("observation_id"),
                "vital_profile_id": (
                    medical_record.get("vital_profiles", [{}])[-1].get("profile_id")
                    if medical_record.get("vital_profiles") else None
                ),
                "finding_ids": [
                    item["finding_id"]
                    for item in medical_record.get("findings", [])
                    if item.get("finding_id")
                ],
            },
        }

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

    def _query_focus(self, queries):
        total_impressions = sum(float(item.get("impressions", 0)) for item in queries)
        if total_impressions <= 0 or len(queries) < 2:
            return None
        sorted_queries = sorted(
            queries,
            key=lambda item: float(item.get("impressions", 0)),
            reverse=True,
        )
        top_impressions = sum(
            float(item.get("impressions", 0))
            for item in sorted_queries[:3]
        )
        share = top_impressions / total_impressions
        if share >= self.t["query_concentration_ratio"]:
            return {
                "queries": [
                    item.get("query")
                    for item in sorted_queries[:3]
                    if item.get("query")
                ],
                "impression_share": round(share, 4),
            }
        return None

    def _resilience_ok(self, score):
        return (
            score is None
            or score >= self.t["competition_resilience_min"]
        )

    @staticmethod
    def _vital_sign_score(medical_record, code):
        if not medical_record.get("vital_profiles"):
            return None
        signs = medical_record["vital_profiles"][-1].get("signs", [])
        for item in signs:
            if item.get("code") == code and item.get("score") is not None:
                return int(round(item["score"]))
        return None

    @staticmethod
    def _latest_search_observation(medical_record):
        items = [
            item for item in medical_record.get("observations", [])
            if item.get("observation_type") in {
                "SEARCH_CONSOLE",
                "SINGLE_CASE_REQUEST",
                "CURRENT_PERFORMANCE",
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
                "clicks": 0.0,
                "impressions": 0.0,
                "ctr": 0.0,
                "position": None,
                "competition_resilience": None,
                "content_integrity": None,
                "query_focus": None,
                "low_sample": True,
            },
            "protections": {
                "winner_query_protected": False,
                "winner_query": None,
                "aggressive_rewrite_allowed": False,
                "new_article_allowed": False,
            },
            "trace": {
                "search_observation_id": None,
                "vital_profile_id": None,
                "finding_ids": [],
            },
        }
