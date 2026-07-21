"""Chat / provider message types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.enums import MessageRole


class ChatMessage(BaseModel):
    """A single message exchanged with a model provider."""

    model_config = ConfigDict(extra="forbid")

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
