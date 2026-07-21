"""Discriminated ``AgentAction`` union — LLM decision surface."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.plan import ExecutionPlan


class InvokeToolAction(BaseModel):
    """Ask the runtime to execute a registered tool."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["invoke_tool"] = "invoke_tool"
    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str | None = Field(
        default=None,
        description="Short public rationale (not private chain-of-thought).",
    )


class RevisePlanAction(BaseModel):
    """Replace the current execution plan."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["revise_plan"] = "revise_plan"
    plan: ExecutionPlan
    reason: str = Field(min_length=1)


class RequestApprovalAction(BaseModel):
    """Pause for human/policy approval before a risky operation."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["request_approval"] = "request_approval"
    purpose: str = Field(min_length=1)
    risk_summary: str = Field(min_length=1)
    proposed_action: dict[str, Any] = Field(default_factory=dict)


class RunTestsAction(BaseModel):
    """Request the test-loop path (tool selection left to runtime/policy)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["run_tests"] = "run_tests"
    selector: str | None = Field(
        default=None,
        description="Optional test selector / node id hint.",
    )
    rationale: str | None = None


class RequestReviewAction(BaseModel):
    """Trigger the separate reviewer role (ADR 0004)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["request_review"] = "request_review"
    focus: list[str] = Field(default_factory=list)
    rationale: str | None = None


class FinishAction(BaseModel):
    """Declare the task complete from the actor's perspective."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["finish"] = "finish"
    summary: str = Field(min_length=1)
    success: bool = True


class AbortAction(BaseModel):
    """Abort the run with a public reason."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["abort"] = "abort"
    reason: str = Field(min_length=1)


AgentAction = Annotated[
    InvokeToolAction
    | RevisePlanAction
    | RequestApprovalAction
    | RunTestsAction
    | RequestReviewAction
    | FinishAction
    | AbortAction,
    Field(discriminator="type"),
]
