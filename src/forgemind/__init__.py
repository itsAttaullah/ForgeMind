"""ForgeMind — Autonomous Software Engineering Agent runtime.

Phase 1 exposes core domain types and protocols. The agent loop is not
implemented yet (see ROADMAP Phase 6+).
"""

from __future__ import annotations

from forgemind.core import (
    AgentAction,
    EngineeringReport,
    ExecutionPlan,
    InvalidActionError,
    RunState,
    RunStatus,
    TaskSpec,
    parse_agent_action,
)

__version__ = "0.1.0.dev0"

__all__ = [
    "AgentAction",
    "EngineeringReport",
    "ExecutionPlan",
    "InvalidActionError",
    "RunState",
    "RunStatus",
    "TaskSpec",
    "__version__",
    "parse_agent_action",
]
