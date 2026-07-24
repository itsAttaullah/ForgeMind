"""State machine transition tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from forgemind.agent import can_transition, transition
from forgemind.core.enums import RunStatus, TaskMode
from forgemind.core.errors import IllegalTransitionError
from forgemind.core.state import RunState
from forgemind.core.task import TaskSpec


def _state(status: RunStatus) -> RunState:
    return RunState(
        status=status,
        task=TaskSpec(goal="Explain repo", workspace_root=Path("."), mode=TaskMode.EXPLAIN),
    )


def test_legal_happy_path_edges() -> None:
    assert can_transition(RunStatus.RECEIVED, RunStatus.ANALYZING)
    assert can_transition(RunStatus.ANALYZING, RunStatus.PLANNING)
    assert can_transition(RunStatus.PLANNING, RunStatus.INVESTIGATING)
    assert can_transition(RunStatus.INVESTIGATING, RunStatus.REFLECTING)
    assert can_transition(RunStatus.REFLECTING, RunStatus.INVESTIGATING)
    assert can_transition(RunStatus.INVESTIGATING, RunStatus.REPORTING)
    assert can_transition(RunStatus.REPORTING, RunStatus.COMPLETED)
    assert can_transition(RunStatus.ACTING, RunStatus.TESTING)
    assert can_transition(RunStatus.TESTING, RunStatus.REFLECTING)
    assert can_transition(RunStatus.REFLECTING, RunStatus.ACTING)


def test_illegal_transition_raises() -> None:
    state = _state(RunStatus.RECEIVED)
    with pytest.raises(IllegalTransitionError):
        transition(state, RunStatus.COMPLETED)


def test_terminal_cannot_leave() -> None:
    state = _state(RunStatus.COMPLETED)
    with pytest.raises(IllegalTransitionError):
        transition(state, RunStatus.ANALYZING)
