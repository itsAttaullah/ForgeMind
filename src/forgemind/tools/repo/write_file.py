"""Write a text file under the workspace jail."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forgemind.core.enums import Permission, RiskClass
from forgemind.core.tools import ToolManifest, ToolParameterSchema
from forgemind.policy.paths import resolve_workspace_path
from forgemind.tools.base import BaseTool
from forgemind.tools.repo._paths import relative_posix, workspace_root_or_raise

DEFAULT_MAX_BYTES = 200_000


class WriteFileTool(BaseTool):
    """Create or overwrite a text file inside the workspace."""

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace_root = workspace_root_or_raise(workspace_root)

    @property
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            name="repo.write_file",
            description="Create or overwrite a text file in the workspace.",
            risk_class=RiskClass.WRITE,
            permissions=[Permission.REPO_WRITE],
            parameters=ToolParameterSchema(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative file path.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file contents to write.",
                    },
                    "create_parents": {
                        "type": "boolean",
                        "description": "Create parent directories if missing (default: true).",
                    },
                },
                required=["path", "content"],
                additional_properties=False,
            ),
        )

    async def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        rel = str(arguments["path"])
        content = str(arguments["content"])
        create_parents = bool(arguments.get("create_parents", True))
        encoded = content.encode("utf-8")
        if len(encoded) > DEFAULT_MAX_BYTES:
            raise ValueError(f"content exceeds {DEFAULT_MAX_BYTES} bytes")

        absolute = resolve_workspace_path(self._workspace_root, rel)
        if create_parents:
            absolute.parent.mkdir(parents=True, exist_ok=True)
        elif not absolute.parent.is_dir():
            raise ValueError(f"parent directory does not exist: {absolute.parent}")

        existed = absolute.exists()
        absolute.write_text(content, encoding="utf-8", newline="\n")
        return {
            "path": relative_posix(self._workspace_root, absolute),
            "bytes_written": len(encoded),
            "created": not existed,
            "overwritten": existed,
        }
