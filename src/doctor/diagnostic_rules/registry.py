from __future__ import annotations

from pathlib import Path
import json

from .models import DiagnosticRule


class DiagnosticRuleRegistry:
    def __init__(self, rules: list[DiagnosticRule]) -> None:
        self.rules = tuple(rules)
        ids = [rule.rule_id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate diagnostic rule ID")

    @classmethod
    def from_file(cls, path: str | Path) -> "DiagnosticRuleRegistry":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([
            DiagnosticRule.from_dict(item)
            for item in data["rules"]
        ])

    def enabled_rules(self) -> tuple[DiagnosticRule, ...]:
        return tuple(rule for rule in self.rules if rule.enabled)
