"""Policy decision types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.enums import Permission, RiskClass


class PolicyRequest(BaseModel):
    """Input to a policy authorization check."""

    model_config = ConfigDict(extra="forbid")

    permissions: list[Permission] = Field(default_factory=list)
    risk_class: RiskClass = RiskClass.READ
    path: str | None = None
    tool_requires_approval: bool = False


class PolicyDecision(BaseModel):
    """Authorization outcome for a policy request."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    requires_approval: bool = False
    reason: str
    missing_permissions: list[Permission] = Field(default_factory=list)
