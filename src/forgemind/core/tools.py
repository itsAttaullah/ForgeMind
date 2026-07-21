"""Tool call / result envelopes (data contracts only)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.enums import Permission, RiskClass, ToolResultStatus


class ToolParameterSchema(BaseModel):
    """Minimal JSON-schema-like parameter description for a tool."""

    model_config = ConfigDict(extra="forbid")

    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool = False


class ToolManifest(BaseModel):
    """Declarative tool metadata used by the registry (Phase 4)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_class: RiskClass = RiskClass.READ
    permissions: list[Permission] = Field(default_factory=list)
    parameters: ToolParameterSchema = Field(default_factory=ToolParameterSchema)
    requires_approval: bool = False


class ToolCall(BaseModel):
    """Validated request to invoke a registered tool."""

    model_config = ConfigDict(extra="forbid")

    call_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Normalized tool execution outcome."""

    model_config = ConfigDict(extra="forbid")

    call_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    status: ToolResultStatus
    output: Any = None
    error: str | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Observation(BaseModel):
    """Model-facing observation derived from a tool result or system event."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, description="tool:<name> | system | review")
    summary: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)
    related_call_id: str | None = None
