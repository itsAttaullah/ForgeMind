"""Protocol structural typing smoke tests."""

from __future__ import annotations

from forgemind.core import (
    MemoryStore,
    ModelProvider,
    Planner,
    Reflector,
    Reviewer,
    Tool,
    ToolManifest,
    ToolRegistry,
)


class _FakeTool:
    @property
    def manifest(self) -> ToolManifest:
        return ToolManifest(name="noop", description="No-op tool")

    async def execute(self, call):  # type: ignore[no-untyped-def]
        raise NotImplementedError


def test_tool_protocol_runtime_checkable() -> None:
    assert isinstance(_FakeTool(), Tool)


def test_protocols_are_importable() -> None:
    # Ensure the public protocol names remain stable (Phase 1 naming freeze).
    assert ModelProvider.__name__ == "ModelProvider"
    assert ToolRegistry.__name__ == "ToolRegistry"
    assert MemoryStore.__name__ == "MemoryStore"
    assert Planner.__name__ == "Planner"
    assert Reflector.__name__ == "Reflector"
    assert Reviewer.__name__ == "Reviewer"
