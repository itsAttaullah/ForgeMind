"""Edit a text file by exact string replacement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forgemind.core.enums import Permission, RiskClass
from forgemind.core.errors import ToolExecutionError
from forgemind.core.tools import ToolManifest, ToolParameterSchema
from forgemind.policy.paths import resolve_workspace_path
from forgemind.tools.base import BaseTool
from forgemind.tools.repo._paths import ensure_file, relative_posix, workspace_root_or_raise


class EditFileTool(BaseTool):
    """Replace an exact substring in a workspace text file."""

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace_root = workspace_root_or_raise(workspace_root)

    @property
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            name="repo.edit_file",
            description="Replace an exact string in a workspace text file.",
            risk_class=RiskClass.WRITE,
            permissions=[Permission.REPO_WRITE],
            parameters=ToolParameterSchema(
                type="object",
                properties={
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative file path.",
                    },
                    "old_string": {
                        "type": "string",
                        "description": "Exact text to find.",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "Replacement text.",
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "Replace all occurrences (default: false).",
                    },
                },
                required=["path", "old_string", "new_string"],
                additional_properties=False,
            ),
        )

    async def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        rel = str(arguments["path"])
        old = str(arguments["old_string"])
        new = str(arguments["new_string"])
        replace_all = bool(arguments.get("replace_all", False))
        if old == "":
            raise ValueError("old_string must not be empty")

        absolute = resolve_workspace_path(self._workspace_root, rel)
        ensure_file(absolute)
        original = absolute.read_text(encoding="utf-8")
        count = original.count(old)
        if count == 0:
            raise ToolExecutionError(f"old_string not found in {rel}")
        if count > 1 and not replace_all:
            raise ToolExecutionError(
                f"old_string found {count} times; pass replace_all=true or make it unique"
            )

        updated = original.replace(old, new) if replace_all else original.replace(old, new, 1)
        absolute.write_text(updated, encoding="utf-8", newline="\n")
        return {
            "path": relative_posix(self._workspace_root, absolute),
            "replacements": count if replace_all else 1,
            "replace_all": replace_all,
        }
