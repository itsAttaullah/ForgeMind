"""Path confinement and glob matching for policy checks."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from forgemind.core.errors import PermissionDeniedError


def normalize_workspace_root(workspace_root: str | Path) -> Path:
    """Return a resolved absolute workspace root."""

    root = Path(workspace_root).expanduser().resolve()
    if not root.exists():
        # Allow non-existent roots in unit tests; still normalize.
        root = root.resolve()
    return root


def resolve_workspace_path(workspace_root: str | Path, target: str | Path) -> Path:
    """Resolve ``target`` under ``workspace_root`` and reject escapes.

    Raises:
        PermissionDeniedError: If the path escapes the workspace jail.
    """

    root = normalize_workspace_root(workspace_root)
    candidate = Path(target)
    absolute = candidate if candidate.is_absolute() else (root / candidate)
    resolved = absolute.resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PermissionDeniedError(f"path escapes workspace root: {target} (root={root})") from exc

    return resolved


def to_workspace_relative(workspace_root: str | Path, absolute_path: Path) -> str:
    """Return a POSIX-style path relative to the workspace root."""

    root = normalize_workspace_root(workspace_root)
    relative = absolute_path.resolve().relative_to(root)
    return relative.as_posix()


def matches_any(relative_posix: str, patterns: list[str]) -> bool:
    """Return True if ``relative_posix`` matches any glob ``patterns``."""

    path = PurePosixPath(relative_posix)
    name = path.name
    for pattern in patterns:
        normalized = pattern.replace("\\", "/")
        candidates = [normalized]
        if normalized.startswith("**/"):
            candidates.append(normalized[3:])
        for candidate in candidates:
            if path.match(candidate) or PurePosixPath(name).match(candidate):
                return True
            if candidate in {relative_posix, name}:
                return True
    return False


def is_path_allowed(
    *,
    workspace_root: str | Path,
    target: str | Path,
    allowlist: list[str],
    denylist: list[str],
) -> tuple[bool, str]:
    """Evaluate allow/deny rules for a path under the workspace.

    Returns ``(allowed, reason)``.
    """

    try:
        absolute = resolve_workspace_path(workspace_root, target)
    except PermissionDeniedError as exc:
        return False, str(exc)

    relative = to_workspace_relative(workspace_root, absolute)

    if denylist and matches_any(relative, denylist):
        return False, f"path denied by denylist: {relative}"

    if allowlist and not matches_any(relative, allowlist):
        return False, f"path not permitted by allowlist: {relative}"

    return True, f"path allowed: {relative}"
