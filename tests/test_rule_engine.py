from __future__ import annotations

import types

import pytest

from backend.app.services.rule_engine import (
    _apply_operator,
    evaluate_aggregate_rules,
    evaluate_row_rules,
)


def _rule(**kwargs):
    """Create a lightweight rule-like namespace for unit testing (no DB needed)."""
    defaults = dict(id=1, is_active=True, is_system=False, order=1, field="horas_individuais",
                    operator="gt", value="24", action="quarentena", description=None)
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestApplyOperator:
    def test_gt_true(self):   assert _apply_operator(25, "gt", "24")
    def test_gt_false(self):  assert not _apply_operator(24, "gt", "24")
    def test_gte_equal(self): assert _apply_operator(24, "gte", "24")
    def test_lt_true(self):   assert _apply_operator(-1, "lt", "0")
    def test_lte_equal(self): assert _apply_operator(0, "lte", "0")
    def test_eq_numeric(self): assert _apply_operator(8.0, "eq", "8")
    def test_eq_string(self):  assert _apply_operator("abc", "eq", "abc")
    def test_neq_numeric(self): assert _apply_operator(7, "neq", "8")
    def test_vazio_none(self):  assert _apply_operator(None, "vazio", None)
    def test_vazio_empty(self): assert _apply_operator("", "vazio", None)
    def test_nao_vazio_value(self): assert _apply_operator("x", "nao_vazio", None)
    def test_nao_vazio_empty_false(self): assert not _apply_operator("", "nao_vazio", None)
    def test_contem(self):     assert _apply_operator("hello world", "contem", "world")
    def test_nao_contem(self): assert _apply_operator("hello", "nao_contem", "xyz")
    def test_in_lista(self):   assert _apply_operator("5", "in_lista", "5,6")
    def test_in_lista_miss(self): assert not _apply_operator("3", "in_lista", "5,6")
    def test_bad_operator(self): assert not _apply_operator(1, "unknown_op", "1")
    def test_type_error_returns_false(self): assert not _apply_operator(None, "gt", "24")


class TestEvaluateRowRules:
    def test_no_rules_returns_none(self):
        result = evaluate_row_rules([], {"horas_individuais": 8.0})
        assert result.final_action is None
        assert result.matches == []

    def test_inactive_rule_ignored(self):
        rule = _rule(id=1, is_active=False, field="horas_individuais", operator="gt",
                     value="0", action="quarentena")
        result = evaluate_row_rules([rule], {"horas_individuais": 8.0})
        assert result.final_action is None

    def test_aggregate_field_skipped(self):
        rule = _rule(id=1, is_active=True, field="soma_diaria", operator="gt",
                     value="0", action="warning")
        result = evaluate_row_rules([rule], {"soma_diaria": 30.0})
        assert result.final_action is None

    def test_quarentena_triggered(self):
        rule = _rule(id=1, field="horas_individuais", operator="gt", value="24",
                     action="quarentena", description="Too many hours")
        result = evaluate_row_rules([rule], {"horas_individuais": 25.0})
        assert result.final_action == "quarentena"
        assert len(result.matches) == 1
        assert result.matches[0].rule_id == 1

    def test_warning_triggered(self):
        rule = _rule(id=2, field="dia_semana", operator="in_lista", value="5,6",
                     action="warning", description="Weekend")
        result = evaluate_row_rules([rule], {"dia_semana": 5})
        assert result.final_action == "warning"

    def test_info_triggered_for_empty_pep(self):
        rule = _rule(id=3, field="pep_wbs", operator="vazio", value=None,
                     action="info", description="No PEP")
        result = evaluate_row_rules([rule], {"pep_wbs": None})
        assert result.final_action == "info"

    def test_highest_rank_wins(self):
        r_info = _rule(id=1, field="pep_wbs", operator="vazio", value=None, action="info")
        r_q    = _rule(id=2, field="horas_individuais", operator="gt", value="24", action="quarentena")
        result = evaluate_row_rules([r_info, r_q], {"pep_wbs": None, "horas_individuais": 25.0})
        assert result.final_action == "quarentena"
        assert len(result.matches) == 2

    def test_reason_joins_messages(self):
        r1 = _rule(id=1, field="horas_individuais", operator="gt", value="24",
                   action="quarentena", description="Over 24h")
        r2 = _rule(id=2, field="pep_wbs", operator="vazio", value=None,
                   action="info", description="No PEP")
        result = evaluate_row_rules([r1, r2], {"horas_individuais": 25.0, "pep_wbs": None})
        assert "Over 24h" in result.reason
        assert "No PEP" in result.reason


class TestEvaluateAggregateRules:
    def test_no_rules(self):
        assert evaluate_aggregate_rules([], 30.0, 70.0) == []

    def test_daily_warning(self):
        rule = _rule(id=3, field="soma_diaria", operator="gt", value="24", action="warning")
        matches = evaluate_aggregate_rules([rule], 25.0, 30.0)
        assert len(matches) == 1
        assert matches[0].action == "warning"

    def test_weekly_warning(self):
        rule = _rule(id=4, field="soma_semanal", operator="gt", value="60", action="warning")
        matches = evaluate_aggregate_rules([rule], 10.0, 61.0)
        assert len(matches) == 1

    def test_aggregate_quarentena_capped_to_warning(self):
        rule = _rule(id=5, field="soma_diaria", operator="gt", value="10", action="quarentena")
        matches = evaluate_aggregate_rules([rule], 11.0, 0.0)
        assert matches[0].action == "warning"  # capped

    def test_non_aggregate_field_skipped(self):
        rule = _rule(id=6, field="horas_individuais", operator="gt", value="0", action="warning")
        matches = evaluate_aggregate_rules([rule], 30.0, 0.0)
        assert matches == []

    def test_inactive_rule_ignored(self):
        rule = _rule(id=7, field="soma_diaria", operator="gt", value="0",
                     action="warning", is_active=False)
        assert evaluate_aggregate_rules([rule], 30.0, 0.0) == []
