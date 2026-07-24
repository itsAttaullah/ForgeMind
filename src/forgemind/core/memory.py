"""Memory snapshot types (working + retrieved long-term)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.plan import ExecutionPlan
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.review import ReviewReport
from forgemind.core.tools import Observation


class WorkingMemory(BaseModel):
    """Run-scoped working memory."""

    model_config = ConfigDict(extra="forbid")

    task_brief: str = ""
    plan: ExecutionPlan | None = None
    files_inspected: list[str] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    reflections: list[ReflectionSummary] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    test_summaries: list[str] = Field(default_factory=list)
    last_review: ReviewReport | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LongTermMemoryItem(BaseModel):
    """One retrieved long-term memory record (never raw CoT)."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    content: str = Field(min_length=1)
    kind: str = Field(default="fact", min_length=1)
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySnapshot(BaseModel):
    """Budget-aware slice injected into decision roles."""

    model_config = ConfigDict(extra="forbid")

    working: WorkingMemory = Field(default_factory=WorkingMemory)
    long_term: list[LongTermMemoryItem] = Field(default_factory=list)
