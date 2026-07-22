"""Search workspace text files for a query string."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from forgemind.core.enums import Permission, RiskClass
from forgemind.core.tools import ToolManifest, ToolParameterSchema
from forgemind.policy.paths import resolve_workspace_path
from forgemind.tools.base import BaseTool
from forgemind.tools.repo._paths import (
    DEFAULT_SKIP_DIR_NAMES,
    relative_posix,
    workspace_root_or_raise,
)

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".rs",
    ".go",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".sh",
    ".ps1",
    ".bat",
    ".csv",
}

EXTENSIONLESS_TEXT_NAMES = {"Makefile", "LICENSE", "Dockerfile", "README"}


def _is_searchable_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    return path.name in EXTENSIONLESS_TEXT_NAMES


class SearchFilesTool(BaseTool):
    """Case-sensitive/insensitive substring search across text files."""

    def __init__(self, workspace_root: str | Path) -> None:
        self._workspace_root = workspace_root_or_raise(workspace_root)

    @property
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            name="repo.search",
            description="Search workspace text files for a query string.",
            risk_class=RiskClass.READ,
            permissions=[Permission.REPO_READ],
            parameters=ToolParameterSchema(
                type="object",
                properties={
                    "query": {
                        "type": "string",
                        "description": "Substring to search for.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative root to search (default: '.').",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether matching is case-sensitive (default: false).",
                    },
                    "max_matches": {
                        "type": "integer",
                        "description": "Maximum matches to return (default: 50).",
                    },
                    "max_file_bytes": {
                        "type": "integer",
                        "description": "Skip files larger than this many bytes (default: 200000).",
                    },
                },
                required=["query"],
                additional_properties=False,
            ),
        )

    async def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments["query"])
        if not query:
            raise ValueError("query must not be empty")
        rel = str(arguments.get("path") or ".")
        case_sensitive = bool(arguments.get("case_sensitive", False))
        max_matches = int(arguments.get("max_matches", 50))
        max_file_bytes = int(arguments.get("max_file_bytes", 200_000))
        if max_matches < 1:
            raise ValueError("max_matches must be >= 1")

        start = resolve_workspace_path(self._workspace_root, rel)
        needle = query if case_sensitive else query.lower()
        matches: list[dict[str, Any]] = []
        truncated = False

        files = [start] if start.is_file() else sorted(start.rglob("*"))
        for current in files:
            if current.is_dir():
                continue
            if any(part in DEFAULT_SKIP_DIR_NAMES for part in current.parts):
                continue
            if not _is_searchable_file(current):
                continue
            try:
                if current.stat().st_size > max_file_bytes:
                    continue
                text = current.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for line_no, line in enumerate(text.splitlines(), start=1):
                haystack = line if case_sensitive else line.lower()
                if needle not in haystack:
                    continue
                matches.append(
                    {
                        "path": relative_posix(self._workspace_root, current),
                        "line": line_no,
                        "text": line[:500],
                    }
                )
                if len(matches) >= max_matches:
                    truncated = True
                    break
            if truncated:
                break

        return {
            "query": query,
            "case_sensitive": case_sensitive,
            "matches": matches,
            "count": len(matches),
            "truncated": truncated,
        }
