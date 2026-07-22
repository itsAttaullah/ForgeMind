"""Base helpers for building tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any

from forgemind.core.enums import ToolResultStatus
from forgemind.core.errors import ToolExecutionError, ValidationError
from forgemind.core.tools import ToolCall, ToolManifest, ToolResult
from forgemind.tools.validation import validate_tool_arguments


class BaseTool(ABC):
    """Abstract tool with argument validation and timed execution."""

    @property
    @abstractmethod
    def manifest(self) -> ToolManifest:
        """Return declarative tool metadata."""

    async def execute(self, call: ToolCall) -> ToolResult:
        """Validate arguments, run the tool, and wrap outcomes as ``ToolResult``."""

        started = perf_counter()
        try:
            if call.tool_name != self.manifest.name:
                raise ValidationError(
                    f"call tool_name '{call.tool_name}' does not match '{self.manifest.name}'"
                )
            arguments = validate_tool_arguments(self.manifest.parameters, call.arguments)
            output = await self.run(arguments)
            return ToolResult(
                call_id=call.call_id,
                tool_name=self.manifest.name,
                status=ToolResultStatus.SUCCESS,
                output=output,
                duration_ms=_elapsed_ms(started),
            )
        except ValidationError as exc:
            return ToolResult(
                call_id=call.call_id,
                tool_name=self.manifest.name,
                status=ToolResultStatus.ERROR,
                error=str(exc),
                duration_ms=_elapsed_ms(started),
            )
        except ToolExecutionError as exc:
            return ToolResult(
                call_id=call.call_id,
                tool_name=self.manifest.name,
                status=ToolResultStatus.ERROR,
                error=str(exc),
                duration_ms=_elapsed_ms(started),
            )
        except Exception as exc:
            return ToolResult(
                call_id=call.call_id,
                tool_name=self.manifest.name,
                status=ToolResultStatus.ERROR,
                error=f"unexpected tool failure: {exc}",
                duration_ms=_elapsed_ms(started),
            )

    @abstractmethod
    async def run(self, arguments: dict[str, Any]) -> Any:
        """Execute the tool with validated arguments and return serializable output."""


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)
