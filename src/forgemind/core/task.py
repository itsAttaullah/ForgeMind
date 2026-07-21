"""Task intake types."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from forgemind.core.enums import Permission, TaskMode


class TaskSpec(BaseModel):
    """User-submitted software engineering task.

    The runtime binds a workspace and mode; the LLM never receives a raw host
    handle — only serialized task fields and tool observations.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    goal: str = Field(min_length=1, description="Natural-language engineering goal.")
    workspace_root: Path = Field(description="Absolute or resolved workspace path.")
    mode: TaskMode = TaskMode.CUSTOM
    constraints: list[str] = Field(default_factory=list)
    permissions: list[Permission] = Field(
        default_factory=lambda: [Permission.REPO_READ],
        description="Capability tokens granted for this run.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("goal")
    @classmethod
    def _goal_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("goal must not be blank")
        return cleaned

    @field_validator("workspace_root", mode="before")
    @classmethod
    def _coerce_workspace(cls, value: str | Path) -> Path:
        return Path(value)
