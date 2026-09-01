from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuleCondition:
    source: str
    field: str
    operator: str
    value: Any
    code: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuleCondition":
        return cls(
            source=data["source"],
            code=data.get("code"),
            field=data["field"],
            operator=data["operator"],
            value=data.get("value"),
        )


@dataclass(frozen=True)
class DiagnosticRule:
    rule_id: str
    rule_version: str
    enabled: bool
    priority: int
    diagnosis_code: str
    condition_logic: str
    conditions: tuple[RuleCondition, ...]
    base_confidence: int
    severity: str
    explanation_template: str
    mutual_exclusion_group: str | None = None
    specificity: int = 0
    tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagnosticRule":
        rule = cls(
            rule_id=data["rule_id"],
            rule_version=data["rule_version"],
            enabled=bool(data["enabled"]),
            priority=int(data["priority"]),
            diagnosis_code=data["diagnosis_code"],
            condition_logic=data["condition_logic"],
            conditions=tuple(
                RuleCondition.from_dict(item)
                for item in data["conditions"]
            ),
            base_confidence=int(data["base_confidence"]),
            severity=data["severity"],
            explanation_template=data["explanation_template"],
            mutual_exclusion_group=data.get("mutual_exclusion_group"),
            specificity=int(data.get("specificity", 0)),
            tags=tuple(data.get("tags", [])),
        )
        rule.validate()
        return rule

    def validate(self) -> None:
        if self.condition_logic not in {"ALL", "ANY"}:
            raise ValueError("Unsupported condition logic")
        if not self.conditions:
            raise ValueError("Diagnostic rule must contain conditions")
        if not 0 <= self.base_confidence <= 100:
            raise ValueError("Base confidence must be 0-100")
