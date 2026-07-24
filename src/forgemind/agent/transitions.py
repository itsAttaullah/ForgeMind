"""Run status transition table and guards."""

from __future__ import annotations

from forgemind.core.enums import RunStatus
from forgemind.core.errors import IllegalTransitionError
from forgemind.core.state import RunState

# Legal edges for the ASE run state machine (ADR 0003).
ALLOWED_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.RECEIVED: frozenset({RunStatus.ANALYZING, RunStatus.FAILED, RunStatus.ABORTED}),
    RunStatus.ANALYZING: frozenset(
        {
            RunStatus.PLANNING,
            RunStatus.INVESTIGATING,
            RunStatus.FAILED,
            RunStatus.ABORTED,
        }
    ),
    RunStatus.PLANNING: frozenset({RunStatus.INVESTIGATING, RunStatus.FAILED, RunStatus.ABORTED}),
    RunStatus.INVESTIGATING: frozenset(
        {
            RunStatus.INVESTIGATING,
            RunStatus.ACTING,
            RunStatus.TESTING,
            RunStatus.REFLECTING,
            RunStatus.REPORTING,
            RunStatus.AWAITING_APPROVAL,
            RunStatus.FAILED,
            RunStatus.ABORTED,
        }
    ),
    RunStatus.ACTING: frozenset(
        {
            RunStatus.TESTING,
            RunStatus.REFLECTING,
            RunStatus.REVIEWING,
            RunStatus.AWAITING_APPROVAL,
            RunStatus.FAILED,
            RunStatus.ABORTED,
        }
    ),
    RunStatus.REFLECTING: frozenset(
        {
            RunStatus.INVESTIGATING,
            RunStatus.ACTING,
            RunStatus.TESTING,
            RunStatus.REVIEWING,
            RunStatus.REPORTING,
            RunStatus.AWAITING_APPROVAL,
            RunStatus.FAILED,
            RunStatus.ABORTED,
        }
    ),
    RunStatus.TESTING: frozenset(
        {
            RunStatus.REFLECTING,
            RunStatus.REVIEWING,
            RunStatus.FAILED,
            RunStatus.ABORTED,
        }
    ),
    RunStatus.REVIEWING: frozenset(
        {
            RunStatus.ACTING,
            RunStatus.TESTING,
            RunStatus.INVESTIGATING,
            RunStatus.REPORTING,
            RunStatus.FAILED,
            RunStatus.ABORTED,
        }
    ),
    RunStatus.AWAITING_APPROVAL: frozenset(
        {
            RunStatus.ACTING,
            RunStatus.INVESTIGATING,
            RunStatus.ABORTED,
        }
    ),
    RunStatus.REPORTING: frozenset({RunStatus.COMPLETED, RunStatus.FAILED}),
    RunStatus.COMPLETED: frozenset(),
    RunStatus.FAILED: frozenset(),
    RunStatus.ABORTED: frozenset(),
}


def can_transition(current: RunStatus, target: RunStatus) -> bool:
    """Return True if ``current → target`` is a legal transition."""

    if current == target and current in {
        RunStatus.INVESTIGATING,
        RunStatus.ACTING,
        RunStatus.REFLECTING,
    }:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def transition(state: RunState, target: RunStatus) -> RunState:
    """Apply a legal status transition, updating timestamps.

    Raises:
        IllegalTransitionError: When the edge is not allowed.
    """

    if state.is_terminal and target != state.status:
        raise IllegalTransitionError(
            f"cannot leave terminal state {state.status.value} → {target.value}"
        )
    if not can_transition(state.status, target):
        raise IllegalTransitionError(f"illegal transition: {state.status.value} → {target.value}")
    state.status = target
    state.touch()
    return state
