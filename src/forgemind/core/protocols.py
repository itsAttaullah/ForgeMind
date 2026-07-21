"""Structural protocols (ports) for ForgeMind components.

Implementations land in later phases; Phase 1 freezes the contracts only.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from forgemind.core.memory import LongTermMemoryItem, MemorySnapshot, WorkingMemory
from forgemind.core.plan import ExecutionPlan
from forgemind.core.provider import ProviderRequest, ProviderResponse
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.review import ReviewReport
from forgemind.core.state import RunState
from forgemind.core.tools import Observation, ToolCall, ToolManifest, ToolResult


@runtime_checkable
class ModelProvider(Protocol):
    """Port for LLM chat / structured decision calls."""

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Return a single completion for ``request``."""
        ...


@runtime_checkable
class Tool(Protocol):
    """A single executable capability exposed to the agent."""

    @property
    def manifest(self) -> ToolManifest:
        """Return declarative tool metadata."""
        ...

    async def execute(self, call: ToolCall) -> ToolResult:
        """Execute ``call`` and return a normalized result."""
        ...


@runtime_checkable
class ToolRegistry(Protocol):
    """Lookup surface for registered tools."""

    def get(self, name: str) -> Tool:
        """Return a tool by name or raise KeyError."""
        ...

    def list_manifests(self) -> list[ToolManifest]:
        """Return manifests for all registered tools."""
        ...


@runtime_checkable
class MemoryStore(Protocol):
    """Working + long-term memory port."""

    async def load_working(self, run_id: str) -> WorkingMemory:
        """Load working memory for ``run_id``."""
        ...

    async def save_working(self, run_id: str, memory: WorkingMemory) -> None:
        """Persist working memory for ``run_id``."""
        ...

    async def retrieve_long_term(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[LongTermMemoryItem]:
        """Retrieve summarized long-term items for ``query``."""
        ...

    async def snapshot(self, run_id: str, *, query: str | None = None) -> MemorySnapshot:
        """Build a budget-aware memory snapshot for decision roles."""
        ...


@runtime_checkable
class Planner(Protocol):
    """Creates or revises an ``ExecutionPlan``."""

    async def create_plan(self, state: RunState, memory: MemorySnapshot) -> ExecutionPlan:
        """Create an initial plan for the current run."""
        ...

    async def revise_plan(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        reason: str,
    ) -> ExecutionPlan:
        """Revise the plan given ``reason`` and current memory."""
        ...


@runtime_checkable
class Reflector(Protocol):
    """Produces summary-only reflections after significant actions."""

    async def reflect(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        observation: Observation,
    ) -> ReflectionSummary:
        """Evaluate whether the latest observation helped progress."""
        ...


@runtime_checkable
class Reviewer(Protocol):
    """Separate self-review role (ADR 0004)."""

    async def review(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        diff_summary: str,
        focus: list[str] | None = None,
    ) -> ReviewReport:
        """Review proposed changes and return structured findings."""
        ...


@runtime_checkable
class ActionSelector(Protocol):
    """Chooses the next ``AgentAction`` (actor role)."""

    async def select_action(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        available_tools: list[ToolManifest],
    ) -> Any:
        """Return the next validated action (typically ``AgentAction``)."""
        ...
