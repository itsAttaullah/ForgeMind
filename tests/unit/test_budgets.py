"""Budget assertion helper tests."""

from __future__ import annotations

import pytest

from forgemind.config import (
    BudgetSettings,
    assert_cost_budget,
    assert_repair_budget,
    assert_step_budget,
    assert_tool_budget,
)
from forgemind.core.errors import BudgetExceededError
from forgemind.core.state import BudgetCounters


def test_step_budget_ok_then_exceeded() -> None:
    counters = BudgetCounters(max_steps=2, steps_used=1)
    assert_step_budget(counters)
    counters.steps_used = 2
    with pytest.raises(BudgetExceededError, match="step budget"):
        assert_step_budget(counters)


def test_tool_and_repair_budgets() -> None:
    counters = BudgetCounters(
        max_tool_calls=1,
        tool_calls_used=1,
        max_repair_iterations=0,
        repair_iterations_used=0,
    )
    with pytest.raises(BudgetExceededError, match="tool-call"):
        assert_tool_budget(counters)
    with pytest.raises(BudgetExceededError, match="repair"):
        assert_repair_budget(counters)


def test_cost_budget() -> None:
    settings = BudgetSettings(max_cost_usd=1.5)
    assert_cost_budget(settings, 1.0)
    with pytest.raises(BudgetExceededError, match="cost"):
        assert_cost_budget(settings, 1.5)


def test_budget_settings_to_counters() -> None:
    settings = BudgetSettings(max_steps=9, max_tool_calls=8, max_repair_iterations=1)
    counters = settings.to_counters()
    assert counters.max_steps == 9
    assert counters.steps_used == 0
