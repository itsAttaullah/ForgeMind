"""Human approval gate types (ADR 0005)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.enums import ApprovalDecision, RiskClass


class ApprovalRequest(BaseModel):
    """Request presented to a human or automated approval policy."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    risk_class: RiskClass
    risk_summary: str = Field(min_length=1)
    proposed_action: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalResponse(BaseModel):
    """Decision recorded against an ``ApprovalRequest``."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    decision: ApprovalDecision
    comment: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor: str | None = Field(default=None, description="Human id or policy name.")
