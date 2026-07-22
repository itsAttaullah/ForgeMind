"""Tool registry and executor tests."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from forgemind.config import AgentProfile, profile_config
from forgemind.core.enums import Permission, RiskClass, ToolResultStatus
from forgemind.core.errors import ValidationError
from forgemind.core.tools import ToolCall, ToolManifest, ToolParameterSchema
from forgemind.policy import PolicyEngine
from forgemind.tools import (
    BaseTool,
    InMemoryToolRegistry,
    ToolExecutor,
    observation_from_result,
)


class _EchoTool(BaseTool):
    @property
    def manifest(self) -> ToolManifest:
        return ToolManifest(
            name="echo",
            description="Echo text",
            risk_class=RiskClass.READ,
            permissions=[Permission.REPO_READ],
            parameters=ToolParameterSchema(
                properties={"text": {"type": "string"}},
                required=["text"],
            ),
        )

    async def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"echo": arguments["text"]}


def test_registry_register_get_and_duplicate(tmp_path) -> None:
    registry = InMemoryToolRegistry()
    tool = _EchoTool()
    registry.register(tool)
    assert registry.get("echo") is tool
    assert "echo" in registry
    assert len(registry) == 1
    with pytest.raises(ValidationError, match="already registered"):
        registry.register(_EchoTool())


def test_executor_success(tmp_path) -> None:
    registry = InMemoryToolRegistry()
    registry.register(_EchoTool())
    executor = ToolExecutor(
        registry,
        PolicyEngine.from_config(profile_config(AgentProfile.READONLY), workspace_root=tmp_path),
    )
    result = asyncio.run(executor.invoke("echo", {"text": "hi"}, call_id="c1"))
    assert result.status == ToolResultStatus.SUCCESS
    assert result.output == {"echo": "hi"}
    observation = observation_from_result(result)
    assert observation.source == "tool:echo"
    assert "succeeded" in observation.summary


def test_executor_unknown_tool(tmp_path) -> None:
    executor = ToolExecutor(
        InMemoryToolRegistry(),
        PolicyEngine.from_config(profile_config(AgentProfile.READONLY), workspace_root=tmp_path),
    )
    result = asyncio.run(
        executor.execute(ToolCall(call_id="c1", tool_name="missing", arguments={}))
    )
    assert result.status == ToolResultStatus.ERROR
    assert "unknown tool" in (result.error or "")


def test_executor_denies_without_permission(tmp_path) -> None:
    class _Writeish(BaseTool):
        @property
        def manifest(self) -> ToolManifest:
            return ToolManifest(
                name="writeish",
                description="Needs write",
                risk_class=RiskClass.WRITE,
                permissions=[Permission.REPO_WRITE],
            )

        async def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
            return {}

    registry = InMemoryToolRegistry()
    registry.register(_Writeish())
    executor = ToolExecutor(
        registry,
        PolicyEngine.from_config(profile_config(AgentProfile.READONLY), workspace_root=tmp_path),
    )
    result = asyncio.run(executor.invoke("writeish", {}))
    assert result.status == ToolResultStatus.DENIED
    assert "missing permissions" in (result.error or "")
