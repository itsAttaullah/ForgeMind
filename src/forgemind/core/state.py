"""Run state and budget counters."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.enums import RunStatus
from forgemind.core.plan import ExecutionPlan
from forgemind.core.task import TaskSpec


def new_run_id() -> str:
    """Allocate a new opaque run identifier."""

    return str(uuid4())


class BudgetCounters(BaseModel):
    """Consumable budgets tracked on a run."""

    model_config = ConfigDict(extra="forbid")

    max_steps: int = Field(default=50, ge=1)
    steps_used: int = Field(default=0, ge=0)
    max_tool_calls: int = Field(default=200, ge=1)
    tool_calls_used: int = Field(default=0, ge=0)
    max_repair_iterations: int = Field(default=5, ge=0)
    repair_iterations_used: int = Field(default=0, ge=0)


class RunState(BaseModel):
    """Serializable control-plane state for one agent run (ADR 0003)."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    run_id: str = Field(default_factory=new_run_id)
    status: RunStatus = RunStatus.RECEIVED
    task: TaskSpec
    plan: ExecutionPlan | None = None
    budgets: BudgetCounters = Field(default_factory=BudgetCounters)
    current_step_id: str | None = None
    last_error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    def touch(self) -> None:
        """Update ``updated_at`` to now (UTC)."""

        self.updated_at = datetime.now(UTC)

    @property
    def is_terminal(self) -> bool:
        """Return True when the run can no longer transition forward."""

        return self.status in {
            RunStatus.COMPLETED,
            RunStatus.FAILED,
            RunStatus.ABORTED,
        }
