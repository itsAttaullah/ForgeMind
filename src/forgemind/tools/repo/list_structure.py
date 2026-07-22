"""List repository structure under the workspace jail."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forgemind.core.enums import Permission, RiskClass
from forgemind.core.tools import ToolManifest, ToolParameterSchema
from forgemind.tools.base import BaseTool
from forgemind.tools.repo._paths import (
    DEFAULT_SKIP_DIR_NAMES,
    ensure_dir,
    relative_posix,
    workspace_root_or_raise,
)


class ListStructureTool(BaseTool):
    """List files and directories under a workspace-relative path."""

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace_root = workspace_root_or_raise(workspace_root)

    @property
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            name="repo.list_structure",
            description="List files and directories under a workspace path.",
            risk_class=RiskClass.READ,
            permissions=[Permission.REPO_READ],
            parameters=ToolParameterSchema(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative directory (default: '.').",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum directory depth to walk (default: 3).",
                    },
                    "max_entries": {
                        "type": "integer",
                        "description": "Maximum entries to return (default: 200).",
                    },
                },
                required=[],
                additional_properties=False,
            ),
        )

    async def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        rel = str(arguments.get("path") or ".")
        max_depth = int(arguments.get("max_depth", 3))
        max_entries = int(arguments.get("max_entries", 200))
        if max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")

        from forgemind.policy.paths import resolve_workspace_path

        start = resolve_workspace_path(self._workspace_root, rel)
        ensure_dir(start)

        entries: list[dict[str, Any]] = []
        truncated = False
        root_depth = len(start.parts)

        for current in sorted(start.rglob("*")):
            depth = len(current.parts) - root_depth
            if depth > max_depth:
                continue
            if any(part in DEFAULT_SKIP_DIR_NAMES for part in current.parts):
                continue
            kind = "dir" if current.is_dir() else "file"
            entries.append(
                {
                    "path": relative_posix(self._workspace_root, current),
                    "kind": kind,
                    "depth": depth,
                }
            )
            if len(entries) >= max_entries:
                truncated = True
                break

        return {
            "root": relative_posix(self._workspace_root, start)
            if start != self._workspace_root
            else ".",
            "entries": entries,
            "truncated": truncated,
            "count": len(entries),
        }
