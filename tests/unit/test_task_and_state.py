"""Unit tests for TaskSpec and RunState."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from forgemind.core import (
    BudgetCounters,
    ExecutionPlan,
    PlanStep,
    RunState,
    RunStatus,
    TaskMode,
    TaskSpec,
)


def test_task_spec_round_trip(tmp_path: Path) -> None:
    task = TaskSpec(
        goal="Explain the repository structure",
        workspace_root=tmp_path,
        mode=TaskMode.EXPLAIN,
    )
    payload = task.model_dump(mode="json")
    restored = TaskSpec.model_validate(payload)
    assert restored.goal == task.goal
    assert restored.mode == TaskMode.EXPLAIN
    assert Path(restored.workspace_root) == tmp_path


def test_task_spec_rejects_blank_goal(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        TaskSpec(goal="   ", workspace_root=tmp_path)


def test_run_state_serialization(tmp_path: Path) -> None:
    task = TaskSpec(goal="Fix failing tests", workspace_root=tmp_path, mode=TaskMode.FIX)
    plan = ExecutionPlan(
        summary="Locate failing test and patch",
        steps=[
            PlanStep(id="1", title="Reproduce failure", success_criteria=["test output captured"]),
            PlanStep(id="2", title="Apply fix", success_criteria=["tests pass"]),
        ],
    )
    state = RunState(
        status=RunStatus.PLANNING,
        task=task,
        plan=plan,
        budgets=BudgetCounters(max_steps=25),
    )
    assert not state.is_terminal

    raw = state.model_dump(mode="json")
    restored = RunState.model_validate(raw)
    assert restored.run_id == state.run_id
    assert restored.status == RunStatus.PLANNING
    assert restored.plan is not None
    assert restored.plan.steps[0].id == "1"


def test_terminal_statuses(tmp_path: Path) -> None:
    task = TaskSpec(goal="x", workspace_root=tmp_path)
    for status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.ABORTED):
        state = RunState(task=task, status=status)
        assert state.is_terminal
