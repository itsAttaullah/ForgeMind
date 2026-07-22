"""In-memory tool registry."""

from __future__ import annotations

from forgemind.core.errors import ValidationError
from forgemind.core.protocols import Tool
from forgemind.core.tools import ToolManifest


class InMemoryToolRegistry:
    """Register and look up tools by name."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register ``tool``, rejecting duplicate names."""

        name = tool.manifest.name
        if name in self._tools:
            raise ValidationError(f"tool already registered: {name}")
        self._tools[name] = tool

    def get(self, name: str) -> Tool:
        """Return a registered tool or raise ``KeyError``."""

        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {name}") from exc

    def list_manifests(self) -> list[ToolManifest]:
        """Return manifests sorted by tool name."""

        return [self._tools[name].manifest for name in sorted(self._tools)]

    def names(self) -> list[str]:
        """Return registered tool names sorted alphabetically."""

        return sorted(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
