"""Policy engine allow/deny matrix tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from forgemind.config import AgentProfile, profile_config
from forgemind.core.enums import Permission, RiskClass
from forgemind.core.errors import PermissionDeniedError
from forgemind.policy import PolicyEngine, PolicyRequest, resolve_workspace_path


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    return tmp_path


def test_readonly_denies_write_permission(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.READONLY),
        workspace_root=workspace,
    )
    decision = engine.evaluate(
        PolicyRequest(permissions=[Permission.REPO_WRITE], risk_class=RiskClass.WRITE)
    )
    assert decision.allowed is False
    assert Permission.REPO_WRITE in decision.missing_permissions


def test_readonly_allows_read(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.READONLY),
        workspace_root=workspace,
    )
    decision = engine.authorize(
        PolicyRequest(
            permissions=[Permission.REPO_READ],
            risk_class=RiskClass.READ,
            path="src/app.py",
        )
    )
    assert decision.allowed is True
    assert decision.requires_approval is False


def test_denylist_blocks_env(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.STANDARD),
        workspace_root=workspace,
    )
    decision = engine.evaluate(
        PolicyRequest(
            permissions=[Permission.REPO_READ],
            risk_class=RiskClass.READ,
            path=".env",
        )
    )
    assert decision.allowed is False
    assert "denylist" in decision.reason


def test_standard_write_allowed_without_approval(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.STANDARD),
        workspace_root=workspace,
    )
    decision = engine.authorize(
        PolicyRequest(
            permissions=[Permission.REPO_WRITE],
            risk_class=RiskClass.WRITE,
            path="src/app.py",
        )
    )
    assert decision.allowed is True
    assert decision.requires_approval is False


def test_strict_write_requires_approval(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.STRICT),
        workspace_root=workspace,
    )
    decision = engine.authorize(
        PolicyRequest(
            permissions=[Permission.REPO_WRITE],
            risk_class=RiskClass.WRITE,
            path="src/app.py",
        )
    )
    assert decision.allowed is True
    assert decision.requires_approval is True


def test_lockfile_path_requires_approval(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.STANDARD),
        workspace_root=workspace,
    )
    decision = engine.authorize(
        PolicyRequest(
            permissions=[Permission.REPO_WRITE],
            risk_class=RiskClass.WRITE,
            path="pyproject.toml",
        )
    )
    assert decision.requires_approval is True


def test_git_mutation_requires_approval_and_permission(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.STANDARD),
        workspace_root=workspace,
    )
    denied = engine.evaluate(
        PolicyRequest(permissions=[Permission.GIT_WRITE], risk_class=RiskClass.MUTATE_GIT)
    )
    assert denied.allowed is False

    # Even if permission were granted, mutate_git requires approval on standard.
    cfg = profile_config(AgentProfile.STANDARD)
    cfg.policy.permissions.append(Permission.GIT_WRITE)
    engine = PolicyEngine.from_config(cfg, workspace_root=workspace)
    decision = engine.authorize(
        PolicyRequest(permissions=[Permission.GIT_WRITE], risk_class=RiskClass.MUTATE_GIT)
    )
    assert decision.requires_approval is True


def test_path_escape_denied(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.STANDARD),
        workspace_root=workspace,
    )
    outside = workspace.parent / "outside.txt"
    with pytest.raises(PermissionDeniedError, match="escapes workspace"):
        engine.authorize(
            PolicyRequest(
                permissions=[Permission.REPO_READ],
                risk_class=RiskClass.READ,
                path=str(outside),
            )
        )


def test_resolve_workspace_path_ok(workspace: Path) -> None:
    resolved = resolve_workspace_path(workspace, "src/app.py")
    assert resolved == (workspace / "src" / "app.py").resolve()


def test_authorize_raises_on_deny(workspace: Path) -> None:
    engine = PolicyEngine.from_config(
        profile_config(AgentProfile.READONLY),
        workspace_root=workspace,
    )
    with pytest.raises(PermissionDeniedError, match="missing permissions"):
        engine.authorize(
            PolicyRequest(permissions=[Permission.TEST_RUN], risk_class=RiskClass.EXEC)
        )
