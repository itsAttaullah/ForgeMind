"""Built-in profile defaults for ForgeMind."""

from __future__ import annotations

from forgemind.config.models import (
    AgentProfile,
    BudgetSettings,
    ForgeMindConfig,
    PolicySettings,
    ProviderSettings,
)
from forgemind.core.enums import Permission, RiskClass

_DEFAULT_DENYLIST: list[str] = [
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "**/secrets/**",
    "**/*.pem",
    "**/*.key",
    "**/*credentials*",
    ".git/objects/**",
    "**/.git/objects/**",
]

_SENSITIVE_WRITE_PATHS: list[str] = [
    "**/pyproject.toml",
    "**/package-lock.json",
    "**/pnpm-lock.yaml",
    "**/yarn.lock",
    "**/uv.lock",
    "**/Cargo.lock",
    "**/poetry.lock",
]


def default_path_denylist() -> list[str]:
    """Return a copy of the default secret / VCS denylist."""

    return list(_DEFAULT_DENYLIST)


def profile_config(profile: AgentProfile | str) -> ForgeMindConfig:
    """Return a deep copy of the built-in config for ``profile``."""

    normalized = AgentProfile(profile)
    builder = {
        AgentProfile.READONLY: _readonly_config,
        AgentProfile.STANDARD: _standard_config,
        AgentProfile.STRICT: _strict_config,
    }[normalized]
    return builder()


def _readonly_config() -> ForgeMindConfig:
    return ForgeMindConfig(
        profile=AgentProfile.READONLY,
        budgets=BudgetSettings(
            max_steps=40,
            max_tool_calls=120,
            max_repair_iterations=0,
            timeout_seconds=900.0,
            max_cost_usd=None,
        ),
        policy=PolicySettings(
            permissions=[Permission.REPO_READ, Permission.GIT_READ],
            path_allowlist=[],
            path_denylist=default_path_denylist(),
            risk_classes_requiring_approval=[
                RiskClass.WRITE,
                RiskClass.EXEC,
                RiskClass.MUTATE_GIT,
                RiskClass.MUTATE_REMOTE,
            ],
            paths_requiring_approval=list(_SENSITIVE_WRITE_PATHS),
        ),
        provider=ProviderSettings(),
        log_level="INFO",
        require_review_before_completion=False,
    )


def _standard_config() -> ForgeMindConfig:
    return ForgeMindConfig(
        profile=AgentProfile.STANDARD,
        budgets=BudgetSettings(
            max_steps=50,
            max_tool_calls=200,
            max_repair_iterations=5,
            timeout_seconds=1_800.0,
            max_cost_usd=None,
        ),
        policy=PolicySettings(
            permissions=[
                Permission.REPO_READ,
                Permission.REPO_WRITE,
                Permission.TEST_RUN,
                Permission.GIT_READ,
            ],
            path_allowlist=[],
            path_denylist=default_path_denylist(),
            risk_classes_requiring_approval=[
                RiskClass.MUTATE_GIT,
                RiskClass.MUTATE_REMOTE,
            ],
            paths_requiring_approval=list(_SENSITIVE_WRITE_PATHS),
        ),
        provider=ProviderSettings(),
        log_level="INFO",
        require_review_before_completion=True,
    )


def _strict_config() -> ForgeMindConfig:
    return ForgeMindConfig(
        profile=AgentProfile.STRICT,
        budgets=BudgetSettings(
            max_steps=30,
            max_tool_calls=80,
            max_repair_iterations=2,
            timeout_seconds=900.0,
            max_cost_usd=5.0,
        ),
        policy=PolicySettings(
            permissions=[
                Permission.REPO_READ,
                Permission.REPO_WRITE,
                Permission.TEST_RUN,
                Permission.GIT_READ,
            ],
            path_allowlist=[],
            path_denylist=default_path_denylist(),
            risk_classes_requiring_approval=[
                RiskClass.WRITE,
                RiskClass.EXEC,
                RiskClass.MUTATE_GIT,
                RiskClass.MUTATE_REMOTE,
            ],
            paths_requiring_approval=list(_SENSITIVE_WRITE_PATHS),
        ),
        provider=ProviderSettings(),
        log_level="INFO",
        require_review_before_completion=True,
    )
