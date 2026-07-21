"""Budget enforcement helpers."""

from __future__ import annotations

from forgemind.config.models import BudgetSettings
from forgemind.core.errors import BudgetExceededError
from forgemind.core.state import BudgetCounters


def assert_step_budget(counters: BudgetCounters) -> None:
    """Raise if another step would exceed ``max_steps``."""

    if counters.steps_used >= counters.max_steps:
        raise BudgetExceededError(
            f"step budget exceeded ({counters.steps_used}/{counters.max_steps})"
        )


def assert_tool_budget(counters: BudgetCounters) -> None:
    """Raise if another tool call would exceed ``max_tool_calls``."""

    if counters.tool_calls_used >= counters.max_tool_calls:
        raise BudgetExceededError(
            f"tool-call budget exceeded ({counters.tool_calls_used}/{counters.max_tool_calls})"
        )


def assert_repair_budget(counters: BudgetCounters) -> None:
    """Raise if another repair iteration would exceed the repair budget."""

    if counters.repair_iterations_used >= counters.max_repair_iterations:
        raise BudgetExceededError(
            "repair budget exceeded "
            f"({counters.repair_iterations_used}/{counters.max_repair_iterations})"
        )


def assert_cost_budget(settings: BudgetSettings, cost_usd_used: float) -> None:
    """Raise if spent cost meets/exceeds the configured USD cap."""

    if settings.max_cost_usd is None:
        return
    if cost_usd_used >= settings.max_cost_usd:
        raise BudgetExceededError(
            f"cost budget exceeded ({cost_usd_used}/{settings.max_cost_usd} USD)"
        )
