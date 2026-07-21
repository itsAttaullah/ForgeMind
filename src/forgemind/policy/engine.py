"""Permission and path policy engine."""

from __future__ import annotations

from pathlib import Path

from forgemind.config.models import ForgeMindConfig, PolicySettings
from forgemind.core.enums import Permission, RiskClass
from forgemind.core.errors import PermissionDeniedError
from forgemind.policy.decisions import PolicyDecision, PolicyRequest
from forgemind.policy.paths import (
    is_path_allowed,
    matches_any,
    resolve_workspace_path,
    to_workspace_relative,
)


class PolicyEngine:
    """Evaluates tool/action authorization against config policy."""

    def __init__(
        self,
        settings: PolicySettings,
        *,
        workspace_root: str | Path,
    ) -> None:
        self._settings = settings
        self._workspace_root = Path(workspace_root)

    @classmethod
    def from_config(
        cls,
        config: ForgeMindConfig,
        *,
        workspace_root: str | Path,
    ) -> PolicyEngine:
        """Build an engine from a full ``ForgeMindConfig``."""

        return cls(config.policy, workspace_root=workspace_root)

    @property
    def settings(self) -> PolicySettings:
        return self._settings

    def has_permission(self, permission: Permission) -> bool:
        """Return True if ``permission`` is granted."""

        return permission in self._settings.permissions

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        """Evaluate a request without raising."""

        missing = [perm for perm in request.permissions if not self.has_permission(perm)]
        if missing:
            names = ", ".join(perm.value for perm in missing)
            return PolicyDecision(
                allowed=False,
                requires_approval=False,
                reason=f"missing permissions: {names}",
                missing_permissions=missing,
            )

        if request.path is not None:
            allowed, reason = is_path_allowed(
                workspace_root=self._workspace_root,
                target=request.path,
                allowlist=self._settings.path_allowlist,
                denylist=self._settings.path_denylist,
            )
            if not allowed:
                return PolicyDecision(
                    allowed=False,
                    requires_approval=False,
                    reason=reason,
                )

        requires_approval = self._requires_approval(request)
        reason = "allowed (approval required)" if requires_approval else "allowed"
        return PolicyDecision(
            allowed=True,
            requires_approval=requires_approval,
            reason=reason,
        )

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        """Evaluate and raise ``PermissionDeniedError`` when not allowed."""

        decision = self.evaluate(request)
        if not decision.allowed:
            raise PermissionDeniedError(decision.reason)
        return decision

    def _requires_approval(self, request: PolicyRequest) -> bool:
        if request.tool_requires_approval:
            return True
        if request.risk_class in self._settings.risk_classes_requiring_approval:
            return True
        if request.path is None:
            return False
        # Path patterns are matched on workspace-relative POSIX paths.
        absolute = resolve_workspace_path(self._workspace_root, request.path)
        relative = to_workspace_relative(self._workspace_root, absolute)
        return matches_any(relative, self._settings.paths_requiring_approval)


def risk_permissions(risk_class: RiskClass) -> list[Permission]:
    """Map a risk class to the typical required permission tokens."""

    mapping: dict[RiskClass, list[Permission]] = {
        RiskClass.READ: [Permission.REPO_READ],
        RiskClass.WRITE: [Permission.REPO_WRITE],
        RiskClass.EXEC: [Permission.TEST_RUN],
        RiskClass.MUTATE_GIT: [Permission.GIT_WRITE],
        RiskClass.MUTATE_REMOTE: [Permission.GITHUB_WRITE],
    }
    return list(mapping[risk_class])
