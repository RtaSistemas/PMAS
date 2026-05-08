from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.models import ValidationRule

AGGREGATE_FIELDS: frozenset[str] = frozenset({"soma_diaria", "soma_semanal"})
AGGREGATE_ACTIONS_ALLOWED: frozenset[str] = frozenset({"info", "warning"})
ACTION_RANK: dict[str, int] = {"info": 0, "warning": 1, "quarentena": 2, "descarte": 3}
OPERATORS: frozenset[str] = frozenset({
    "gt", "gte", "lt", "lte", "eq", "neq",
    "vazio", "nao_vazio", "contem", "nao_contem", "in_lista",
})


@dataclass
class RuleMatch:
    rule_id: int
    action: str
    message: str


@dataclass
class RowEvalResult:
    final_action: str | None
    matches: list[RuleMatch] = field(default_factory=list)

    @property
    def reason(self) -> str:
        return ", ".join(m.message for m in self.matches)


def evaluate_row_rules(rules: list[ValidationRule], row_fields: dict) -> RowEvalResult:
    matches: list[RuleMatch] = []
    for rule in rules:
        if not rule.is_active or rule.field in AGGREGATE_FIELDS:
            continue
        if _apply_operator(row_fields.get(rule.field), rule.operator, rule.value):
            msg = rule.description or f"{rule.field} {rule.operator} {rule.value}"
            matches.append(RuleMatch(rule_id=rule.id, action=rule.action, message=msg))
    if not matches:
        return RowEvalResult(final_action=None)
    best = max(matches, key=lambda m: ACTION_RANK.get(m.action, 0))
    return RowEvalResult(final_action=best.action, matches=matches)


def evaluate_aggregate_rules(
    rules: list[ValidationRule], daily_total: float, weekly_total: float
) -> list[RuleMatch]:
    field_map = {"soma_diaria": daily_total, "soma_semanal": weekly_total}
    matches: list[RuleMatch] = []
    for rule in rules:
        if not rule.is_active or rule.field not in AGGREGATE_FIELDS:
            continue
        value = field_map[rule.field]
        if _apply_operator(value, rule.operator, rule.value):
            action = rule.action if rule.action in AGGREGATE_ACTIONS_ALLOWED else "warning"
            msg = rule.description or f"{rule.field} {rule.operator} {rule.value}"
            matches.append(RuleMatch(rule_id=rule.id, action=action, message=msg))
    return matches


def _apply_operator(field_value, operator: str, rule_value: str | None) -> bool:
    try:
        if operator in ("gt", "gte", "lt", "lte"):
            fv = float(field_value)
            rv = float(rule_value)
            return {"gt": fv > rv, "gte": fv >= rv, "lt": fv < rv, "lte": fv <= rv}[operator]
        if operator == "eq":
            try:
                return float(field_value) == float(rule_value)
            except (TypeError, ValueError):
                return str(field_value) == str(rule_value)
        if operator == "neq":
            try:
                return float(field_value) != float(rule_value)
            except (TypeError, ValueError):
                return str(field_value) != str(rule_value)
        if operator == "vazio":
            return field_value is None or str(field_value).strip() == ""
        if operator == "nao_vazio":
            return not (field_value is None or str(field_value).strip() == "")
        if operator == "contem":
            return str(rule_value or "").lower() in str(field_value or "").lower()
        if operator == "nao_contem":
            return str(rule_value or "").lower() not in str(field_value or "").lower()
        if operator == "in_lista":
            items = [v.strip() for v in (rule_value or "").split(",")]
            return str(field_value) in items
    except (TypeError, ValueError):
        pass
    return False
