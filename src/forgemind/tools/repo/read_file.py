"""Read a text file under the workspace jail."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forgemind.core.enums import Permission, RiskClass
from forgemind.core.tools import ToolManifest, ToolParameterSchema
from forgemind.policy.paths import resolve_workspace_path
from forgemind.tools.base import BaseTool
from forgemind.tools.repo._paths import ensure_file, relative_posix, workspace_root_or_raise

DEFAULT_MAX_BYTES = 200_000


class ReadFileTool(BaseTool):
    """Read a UTF-8 (or latin-1 fallback) text file inside the workspace."""

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace_root = workspace_root_or_raise(workspace_root)

    @property
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            name="repo.read_file",
            description="Read a text file from the workspace.",
            risk_class=RiskClass.READ,
            permissions=[Permission.REPO_READ],
            parameters=ToolParameterSchema(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative file path.",
                    },
                    "max_bytes": {
                        "type": "integer",
                        "description": "Maximum bytes to read (default: 200000).",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "1-based start line (default: 1).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of lines to return (optional).",
                    },
                },
                required=["path"],
                additional_properties=False,
            ),
        )

    async def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        rel = str(arguments["path"])
        max_bytes = int(arguments.get("max_bytes", DEFAULT_MAX_BYTES))
        offset = int(arguments.get("offset", 1))
        limit = arguments.get("limit")
        if max_bytes < 1:
            raise ValueError("max_bytes must be >= 1")
        if offset < 1:
            raise ValueError("offset must be >= 1")
        if limit is not None:
            limit = int(limit)
            if limit < 1:
                raise ValueError("limit must be >= 1")

        absolute = resolve_workspace_path(self._workspace_root, rel)
        ensure_file(absolute)

        size = absolute.stat().st_size
        truncated = size > max_bytes
        raw = absolute.read_bytes()[:max_bytes]
        try:
            text = raw.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
            encoding = "latin-1"

        lines = text.splitlines()
        start_idx = offset - 1
        if start_idx >= len(lines):
            selected: list[str] = []
        elif limit is None:
            selected = lines[start_idx:]
        else:
            selected = lines[start_idx : start_idx + limit]

        numbered = [{"line": start_idx + i + 1, "text": line} for i, line in enumerate(selected)]
        return {
            "path": relative_posix(self._workspace_root, absolute),
            "encoding": encoding,
            "size_bytes": size,
            "truncated": truncated,
            "offset": offset,
            "lines": numbered,
            "content": "\n".join(selected),
        }
