from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import DiagnosticRule, RuleCondition


class DiagnosticRuleEngine:
    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def evaluate(
        self,
        medical_record: dict[str, Any],
        rules: tuple[DiagnosticRule, ...],
    ) -> dict[str, Any]:
        max_rules = self.policy["evaluation"]["maximum_rules_per_evaluation"]
        ordered = sorted(
            rules[:max_rules],
            key=lambda rule: (-rule.priority, -rule.specificity, rule.rule_id),
        )

        matched = []
        unmatched = 0

        for rule in ordered:
            condition_results = [
                self._evaluate_condition(medical_record, condition)
                for condition in rule.conditions
            ]
            success = (
                all(item["matched"] for item in condition_results)
                if rule.condition_logic == "ALL"
                else any(item["matched"] for item in condition_results)
            )
            if not success:
                unmatched += 1
                continue

            evidence_ids = sorted({
                identifier
                for item in condition_results
                for identifier in item["evidence_ids"]
            })
            finding_ids = sorted({
                identifier
                for item in condition_results
                for identifier in item["finding_ids"]
            })
            low_sample = any(item["low_sample"] for item in condition_results)
            confidence = self._confidence(
                rule,
                evidence_count=len(evidence_ids),
                finding_count=len(finding_ids),
                low_sample=low_sample,
            )
            matched.append({
                "rule_id": rule.rule_id,
                "diagnosis_code": rule.diagnosis_code,
                "priority": rule.priority,
                "specificity": rule.specificity,
                "confidence": confidence,
                "severity": rule.severity,
                "mutual_exclusion_group": rule.mutual_exclusion_group,
                "explanation": rule.explanation_template,
                "evidence_ids": evidence_ids,
                "finding_ids": finding_ids,
                "condition_results": condition_results,
            })

        candidates = self._resolve_conflicts(matched)
        return {
            "matched_rules": matched,
            "diagnosis_candidates": candidates,
            "unmatched_rule_count": unmatched,
        }

    def _evaluate_condition(
        self,
        medical_record: dict[str, Any],
        condition: RuleCondition,
    ) -> dict[str, Any]:
        items = self._source_items(medical_record, condition.source)
        if condition.code:
            items = [
                item for item in items
                if self._item_code(item, condition.source) == condition.code
            ]

        matched_items = [
            item for item in items
            if self._compare(
                self._get_field(item, condition.field),
                condition.operator,
                condition.value,
            )
        ]

        return {
            "source": condition.source,
            "code": condition.code,
            "field": condition.field,
            "operator": condition.operator,
            "expected": condition.value,
            "matched": bool(matched_items),
            "matched_count": len(matched_items),
            "evidence_ids": [
                item["evidence_id"]
                for item in matched_items
                if item.get("evidence_id")
            ],
            "finding_ids": [
                item["finding_id"]
                for item in matched_items
                if item.get("finding_id")
            ],
            "low_sample": any(bool(item.get("low_sample")) for item in matched_items),
        }

    @staticmethod
    def _source_items(medical_record, source):
        mapping = {
            "EVIDENCE": medical_record.get("evidence", []),
            "FINDING": medical_record.get("findings", []),
            "VITAL_SIGN": (
                medical_record.get("vital_profiles", [{}])[-1].get("signs", [])
                if medical_record.get("vital_profiles") else []
            ),
            "OBSERVATION": medical_record.get("observations", []) + [
                {
                    "observation_type": "IMPROVEMENT_FAILURE_ASSESSMENT",
                    "facts": item,
                    "observation_id": item.get("assessment_id"),
                }
                for item in medical_record.get(
                    "improvement_failure_assessments", []
                )
            ] + [
                {
                    "observation_type": "LONG_TERM_DEGRADATION_ASSESSMENT",
                    "facts": item,
                    "observation_id": item.get("assessment_id"),
                }
                for item in medical_record.get(
                    "long_term_degradation_assessments", []
                )
            ] + [
                {
                    "observation_type": "CTR_OPPORTUNITY_ASSESSMENT",
                    "facts": item,
                    "observation_id": item.get("assessment_id"),
                }
                for item in medical_record.get(
                    "ctr_opportunity_assessments", []
                )
            ] + [
                {
                    "observation_type": "POSITION_OPPORTUNITY_ASSESSMENT",
                    "facts": item,
                    "observation_id": item.get("assessment_id"),
                }
                for item in medical_record.get(
                    "position_opportunity_assessments", []
                )
            ] + [
                {
                    "observation_type": "INTENT_DRIFT_ASSESSMENT",
                    "facts": item,
                    "observation_id": item.get("assessment_id"),
                }
                for item in medical_record.get(
                    "intent_drift_assessments", []
                )
            ] + [
                {
                    "observation_type": "FRESHNESS_DECAY_ASSESSMENT",
                    "facts": item,
                    "observation_id": item.get("assessment_id"),
                }
                for item in medical_record.get(
                    "freshness_decay_assessments", []
                )
            ] + [
                {
                    "observation_type": "CANNIBALIZATION_ASSESSMENT",
                    "facts": item,
                    "observation_id": item.get("assessment_id"),
                }
                for item in medical_record.get(
                    "cannibalization_assessments", []
                )
            ],
            "LONGITUDINAL_PROFILE": (
                [medical_record.get("longitudinal_profiles", [])[-1]]
                if medical_record.get("longitudinal_profiles") else []
            ),
            "TREATMENT_HISTORY": [
                item for item in medical_record.get("observations", [])
                if item.get("observation_type") == "TREATMENT_HISTORY"
            ],
            "CONTEXT": [medical_record],
        }
        return list(mapping.get(source, []))

    @staticmethod
    def _item_code(item, source):
        fields = {
            "EVIDENCE": "evidence_code",
            "FINDING": "finding_code",
            "VITAL_SIGN": "code",
            "OBSERVATION": "observation_type",
            "LONGITUDINAL_PROFILE": "profile_status",
            "TREATMENT_HISTORY": "observation_type",
        }
        return item.get(fields.get(source, "code"))

    @staticmethod
    def _get_field(item, path):
        current = item
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    @staticmethod
    def _compare(actual, operator, expected):
        if operator == "EXISTS":
            return actual is not None if expected else actual is None
        if actual is None:
            return False
        if operator == "EQ":
            return actual == expected
        if operator == "NE":
            return actual != expected
        if operator == "GT":
            return actual > expected
        if operator == "GTE":
            return actual >= expected
        if operator == "LT":
            return actual < expected
        if operator == "LTE":
            return actual <= expected
        if operator == "IN":
            return actual in expected
        if operator == "NOT_IN":
            return actual not in expected
        if operator == "CONTAINS":
            return expected in actual
        raise ValueError(f"Unsupported operator: {operator}")

    def _confidence(self, rule, *, evidence_count, finding_count, low_sample):
        confidence_policy = self.policy["confidence"]
        bonus = (
            evidence_count * confidence_policy["evidence_bonus_per_item"]
            + finding_count * confidence_policy["finding_bonus_per_item"]
        )
        bonus = min(bonus, confidence_policy["maximum_bonus"])
        score = rule.base_confidence + bonus
        if low_sample:
            score -= confidence_policy["low_sample_penalty"]
        return max(0, min(100, round(score)))

    def _resolve_conflicts(self, matched):
        by_diagnosis = {}
        for item in matched:
            current = by_diagnosis.get(item["diagnosis_code"])
            if current is None or self._better(item, current):
                by_diagnosis[item["diagnosis_code"]] = item

        by_group = {}
        independent = []
        for item in by_diagnosis.values():
            group = item.get("mutual_exclusion_group")
            if not group:
                independent.append(item)
                continue
            current = by_group.get(group)
            if current is None or self._better(item, current):
                by_group[group] = item

        resolved = independent + list(by_group.values())
        resolved.sort(
            key=lambda item: (
                -item["priority"],
                -item["confidence"],
                -item["specificity"],
                item["rule_id"],
            )
        )
        return [
            {
                "diagnosis_code": item["diagnosis_code"],
                "confidence": item["confidence"],
                "severity": item["severity"],
                "priority": item["priority"],
                "rule_id": item["rule_id"],
                "explanation": item["explanation"],
                "evidence_ids": item["evidence_ids"],
                "finding_ids": item["finding_ids"],
            }
            for item in resolved
        ]

    @staticmethod
    def _better(candidate, current):
        return (
            candidate["priority"],
            candidate["confidence"],
            candidate["specificity"],
            candidate["rule_id"],
        ) > (
            current["priority"],
            current["confidence"],
            current["specificity"],
            current["rule_id"],
        )
