"""Execution plan types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlanStep(BaseModel):
    """One step in an ``ExecutionPlan``."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    success_criteria: list[str] = Field(default_factory=list)
    suspected_paths: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """Structured plan produced/revised by the planner role."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    steps: list[PlanStep] = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("summary")
    @classmethod
    def _summary_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("summary must not be blank")
        return cleaned
