"""Final engineering report and trace event types."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.enums import RunStatus, TraceEventType
from forgemind.core.plan import ExecutionPlan
from forgemind.core.review import ReviewReport


class ChangedFile(BaseModel):
    """One file touched during a run (for reports)."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    change_type: str = Field(default="modified", min_length=1)
    rationale: str | None = None


class EngineeringReport(BaseModel):
    """Final deliverable produced at the end of a successful/failed run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    status: RunStatus
    task_restatement: str = Field(min_length=1)
    plan: ExecutionPlan | None = None
    key_findings: list[str] = Field(default_factory=list)
    changes: list[ChangedFile] = Field(default_factory=list)
    tests_run: list[str] = Field(default_factory=list)
    test_results_summary: str | None = None
    review: ReviewReport | None = None
    residual_risks: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    """Observability event for audit and replay (Phase 10)."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    event_type: TraceEventType
    message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
