"""Self-review report types (ADR 0004)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from forgemind.core.enums import FindingSeverity


class ReviewFinding(BaseModel):
    """One reviewer finding."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    severity: FindingSeverity
    detail: str = Field(min_length=1)
    path: str | None = None
    recommendation: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewReport(BaseModel):
    """Output of the separate reviewer pass."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    findings: list[ReviewFinding] = Field(default_factory=list)
    approve_completion: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_blocking_findings(self) -> bool:
        """Return True when high/critical findings exist."""

        return any(
            finding.severity in {FindingSeverity.HIGH, FindingSeverity.CRITICAL}
            for finding in self.findings
        )
