"""Shared helpers for repository tools."""

from __future__ import annotations

from pathlib import Path

from forgemind.core.errors import ToolExecutionError
from forgemind.policy.paths import (
    normalize_workspace_root,
    resolve_workspace_path,
    to_workspace_relative,
)

DEFAULT_SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".tox",
}


def safe_resolve(workspace_root: Path, relative_path: str) -> Path:
    """Resolve a path under the workspace jail."""

    return resolve_workspace_path(workspace_root, relative_path)


def relative_posix(workspace_root: Path, absolute: Path) -> str:
    """Return workspace-relative POSIX path."""

    return to_workspace_relative(workspace_root, absolute)


def ensure_file(path: Path) -> None:
    """Raise ``ToolExecutionError`` unless ``path`` is an existing file."""

    if not path.exists():
        raise ToolExecutionError(f"file not found: {path}")
    if not path.is_file():
        raise ToolExecutionError(f"not a file: {path}")


def ensure_dir(path: Path) -> None:
    """Raise ``ToolExecutionError`` unless ``path`` is an existing directory."""

    if not path.exists():
        raise ToolExecutionError(f"directory not found: {path}")
    if not path.is_dir():
        raise ToolExecutionError(f"not a directory: {path}")


def workspace_root_or_raise(path: str | Path) -> Path:
    """Normalize and require an existing workspace directory."""

    root = normalize_workspace_root(path)
    if not root.exists() or not root.is_dir():
        raise ToolExecutionError(f"workspace root is not a directory: {root}")
    return root
