"""Policy-aware tool executor."""

from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import uuid4

from forgemind.core.enums import ToolResultStatus
from forgemind.core.tools import Observation, ToolCall, ToolResult
from forgemind.policy.decisions import PolicyRequest
from forgemind.policy.engine import PolicyEngine
from forgemind.tools.registry import InMemoryToolRegistry


class ToolExecutor:
    """Authorize and execute tool calls through the registry + policy engine."""

    def __init__(
        self,
        registry: InMemoryToolRegistry,
        policy: PolicyEngine,
    ) -> None:
        self._registry = registry
        self._policy = policy

    @property
    def registry(self) -> InMemoryToolRegistry:
        return self._registry

    @property
    def policy(self) -> PolicyEngine:
        return self._policy

    async def execute(self, call: ToolCall) -> ToolResult:
        """Authorize then execute ``call``, returning a normalized ``ToolResult``."""

        started = perf_counter()
        try:
            tool = self._registry.get(call.tool_name)
        except KeyError as exc:
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status=ToolResultStatus.ERROR,
                error=str(exc),
                duration_ms=_elapsed_ms(started),
            )

        path = _extract_path_argument(call.arguments)
        decision = self._policy.evaluate(
            PolicyRequest(
                permissions=list(tool.manifest.permissions),
                risk_class=tool.manifest.risk_class,
                path=path,
                tool_requires_approval=tool.manifest.requires_approval,
            )
        )
        if not decision.allowed:
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                status=ToolResultStatus.DENIED,
                error=decision.reason,
                duration_ms=_elapsed_ms(started),
                metadata={"requires_approval": decision.requires_approval},
            )

        result = await tool.execute(call)
        if decision.requires_approval:
            metadata = dict(result.metadata)
            metadata["requires_approval"] = True
            result = result.model_copy(update={"metadata": metadata})
        return result

    async def invoke(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        *,
        call_id: str | None = None,
    ) -> ToolResult:
        """Convenience wrapper that builds a ``ToolCall`` then executes it."""

        call = ToolCall(
            call_id=call_id or str(uuid4()),
            tool_name=tool_name,
            arguments=arguments or {},
        )
        return await self.execute(call)


def observation_from_result(result: ToolResult) -> Observation:
    """Convert a ``ToolResult`` into a model-facing ``Observation``."""

    if result.status == ToolResultStatus.SUCCESS:
        summary = f"{result.tool_name} succeeded"
        details: dict[str, Any] = {"output": result.output}
    elif result.status == ToolResultStatus.DENIED:
        summary = f"{result.tool_name} denied: {result.error or 'permission denied'}"
        details = {"error": result.error}
    else:
        summary = f"{result.tool_name} failed: {result.error or 'unknown error'}"
        details = {"error": result.error}

    return Observation(
        source=f"tool:{result.tool_name}",
        summary=summary,
        details=details,
        related_call_id=result.call_id,
    )


def _extract_path_argument(arguments: dict[str, Any]) -> str | None:
    for key in ("path", "target", "file", "directory"):
        value = arguments.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)
