"""Reflection summary types (safe to persist — no private CoT)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.enums import ReflectionVerdict


class ReflectionSummary(BaseModel):
    """Structured post-action evaluation stored in working memory."""

    model_config = ConfigDict(extra="forbid")

    verdict: ReflectionVerdict
    helped: bool
    learned: str = Field(min_length=1, description="Public summary of what changed.")
    plan_adjustment: str | None = None
    next_hint: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
