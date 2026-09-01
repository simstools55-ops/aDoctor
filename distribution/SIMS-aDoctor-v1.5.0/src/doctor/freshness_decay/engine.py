from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class FreshnessDecayEngine:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy
        self.t = policy["thresholds"]
        self.outdated_codes = set(policy["outdated_signal_codes"])

    def assess(self, medical_record: dict[str, Any]) -> dict[str, Any]:
        patient = medical_record.get("patient", {})
        updated_at_raw = (
            patient.get("article_updated_at")
            or patient.get("updated_at")
        )
        published_at_raw = (
            patient.get("article_published_at")
            or patient.get("published_at")
        )
        effective_date = updated_at_raw or published_at_raw
        days_since_update = self._days_since(effective_date)

        search_observation = self._latest_search_observation(medical_record)
        impressions = 0.0
        winner = None
        low_sample = False
        if search_observation:
            facts = search_observation.get("facts", {})
            metrics = facts.get("metrics", facts)
            impressions = float(metrics.get("impressions", 0))
            low_sample = bool(metrics.get("low_sample", False))
            winner = self._winner_query(facts.get("queries", []))

        freshness_score = self._vital_score(medical_record, "FRESHNESS")
        outdated_findings = [
            item for item in medical_record.get("findings", [])
            if item.get("finding_code") in self.outdated_codes
        ]
        recent_update = (
            days_since_update is not None
            and days_since_update < self.t["recent_update_days"]
        )

        protections = {
            "winner_query_protected": bool(winner),
            "winner_query": winner,
            "aggressive_title_change_allowed": not bool(winner),
            "deletion_allowed": False,
            "preferred_scope": "NONE",
        }
        reasons = []

        if (
            effective_date is None
            and freshness_score is None
            and not outdated_findings
        ):
            classification = "INSUFFICIENT_DATA"
            confidence = 40
            severity = "INFO"
            reasons.append("更新日・鮮度スコア・陳腐化所見が不足しています。")
        elif low_sample and impressions < self.t["minimum_impressions"]:
            classification = "INSUFFICIENT_DATA"
            confidence = 45
            severity = "INFO"
            reasons.append("表示回数が少なく、鮮度劣化の影響を確定できません。")
        elif recent_update:
            classification = "RECENT_UPDATE_OBSERVATION"
            confidence = 82
            severity = "INFO"
            reasons.append("最近更新されているため、再修正より経過観察を優先します。")
        elif winner and outdated_findings:
            classification = "WINNER_QUERY_PROTECTED"
            confidence = 90
            severity = "MILD"
            protections["preferred_scope"] = "LOCAL_FACT_UPDATE"
            reasons.append("主要流入クエリを維持しながら事実情報のみ更新します。")
        elif self._is_severe(days_since_update, freshness_score, outdated_findings):
            classification = "SEVERE_FRESHNESS_DECAY"
            confidence = 94
            severity = "SEVERE"
            protections["preferred_scope"] = "BROAD_REFRESH"
            reasons.append("長期間未更新で、複数の陳腐化シグナルが確認されました。")
        elif self._is_partial(days_since_update, freshness_score, outdated_findings):
            classification = "PARTIAL_FRESHNESS_DECAY"
            confidence = 88
            severity = "MODERATE"
            protections["preferred_scope"] = "LOCAL_FACT_UPDATE"
            reasons.append("一部の情報に鮮度劣化があり、局所更新が適切です。")
        else:
            classification = "FRESH"
            confidence = 84
            severity = "INFO"
            reasons.append("重大な情報鮮度劣化は確認されませんでした。")

        if days_since_update is not None:
            reasons.append(f"最終更新から{days_since_update}日経過しています。")
        if freshness_score is not None:
            reasons.append(f"FRESHNESS Vital Signは{freshness_score}点です。")
        if outdated_findings:
            reasons.append(
                f"陳腐化所見が{len(outdated_findings)}件確認されています。"
            )

        return {
            "classification": classification,
            "confidence": confidence,
            "severity": severity,
            "reasons": reasons,
            "metrics": {
                "days_since_update": days_since_update,
                "freshness_score": freshness_score,
                "outdated_signal_count": len(outdated_findings),
                "outdated_signal_codes": sorted({
                    item.get("finding_code")
                    for item in outdated_findings
                    if item.get("finding_code")
                }),
                "impressions": impressions,
                "low_sample": low_sample,
            },
            "protections": protections,
            "trace": {
                "search_observation_id": (
                    search_observation.get("observation_id")
                    if search_observation else None
                ),
                "vital_profile_id": (
                    medical_record.get("vital_profiles", [{}])[-1].get("profile_id")
                    if medical_record.get("vital_profiles") else None
                ),
                "finding_ids": [
                    item["finding_id"]
                    for item in outdated_findings
                    if item.get("finding_id")
                ],
            },
        }

    def _is_severe(self, days, score, findings):
        return (
            (days is not None and days >= self.t["severe_stale_days"])
            or (score is not None and score <= self.t["severe_freshness_score"])
            or len(findings) >= self.t["critical_outdated_signal_count"]
        )

    def _is_partial(self, days, score, findings):
        return (
            (days is not None and days >= self.t["stale_days"])
            or (score is not None and score < self.t["minimum_freshness_score"])
            or len(findings) >= self.t["outdated_signal_count"]
        )

    @staticmethod
    def _days_since(value):
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(
            0,
            (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days,
        )

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

    @staticmethod
    def _vital_score(medical_record, code):
        if not medical_record.get("vital_profiles"):
            return None
        for item in medical_record["vital_profiles"][-1].get("signs", []):
            if item.get("code") == code and item.get("score") is not None:
                return int(round(item["score"]))
        return None

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
