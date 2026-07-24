"""Configuration models for ForgeMind (Phase 2)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from forgemind.core.enums import Permission, RiskClass
from forgemind.core.state import BudgetCounters


class AgentProfile(StrEnum):
    """Named security / capability profiles."""

    READONLY = "readonly"
    STANDARD = "standard"
    STRICT = "strict"


class BudgetSettings(BaseModel):
    """Run budget limits (control-plane caps)."""

    model_config = ConfigDict(extra="forbid")

    max_steps: int = Field(default=50, ge=1)
    max_tool_calls: int = Field(default=200, ge=1)
    max_repair_iterations: int = Field(default=5, ge=0)
    timeout_seconds: float | None = Field(default=1_800.0, gt=0)
    max_cost_usd: float | None = Field(default=None, ge=0)

    def to_counters(self) -> BudgetCounters:
        """Create fresh consumable counters seeded from these limits."""

        return BudgetCounters(
            max_steps=self.max_steps,
            max_tool_calls=self.max_tool_calls,
            max_repair_iterations=self.max_repair_iterations,
        )


class PolicySettings(BaseModel):
    """Permissions, path rules, and approval triggers."""

    model_config = ConfigDict(extra="forbid")

    permissions: list[Permission] = Field(default_factory=list)
    path_allowlist: list[str] = Field(
        default_factory=list,
        description="Glob patterns relative to workspace. Empty means allow all (minus denylist).",
    )
    path_denylist: list[str] = Field(default_factory=list)
    risk_classes_requiring_approval: list[RiskClass] = Field(default_factory=list)
    paths_requiring_approval: list[str] = Field(
        default_factory=list,
        description="Glob patterns that always require approval when written.",
    )

    @field_validator("permissions", mode="before")
    @classmethod
    def _coerce_permissions(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value


class ProviderKind(StrEnum):
    """Built-in model provider adapters."""

    STUB = "stub"
    OPENAI_COMPATIBLE = "openai_compatible"


class ProviderSettings(BaseModel):
    """Provider-related settings."""

    model_config = ConfigDict(extra="forbid")

    kind: ProviderKind = ProviderKind.STUB
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    base_url: str | None = None
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = Field(default=60.0, gt=0)


class ForgeMindConfig(BaseModel):
    """Top-level runtime configuration."""

    model_config = ConfigDict(extra="forbid")

    profile: AgentProfile = AgentProfile.STANDARD
    budgets: BudgetSettings = Field(default_factory=BudgetSettings)
    policy: PolicySettings = Field(default_factory=PolicySettings)
    provider: ProviderSettings = Field(default_factory=ProviderSettings)
    log_level: str = "INFO"
    require_review_before_completion: bool = False

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned == "":
            raise ValueError("log_level must not be blank")
        return cleaned
