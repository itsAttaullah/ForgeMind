"""Core domain types and contracts for ForgeMind (Phase 1).

This package freezes the public naming surface for ASE data objects and ports.
No runtime orchestration is implemented here.
"""

from __future__ import annotations

from forgemind.core.actions import (
    AbortAction,
    AgentAction,
    FinishAction,
    InvokeToolAction,
    RequestApprovalAction,
    RequestReviewAction,
    RevisePlanAction,
    RunTestsAction,
)
from forgemind.core.approval import ApprovalRequest, ApprovalResponse
from forgemind.core.enums import (
    ApprovalDecision,
    FindingSeverity,
    MessageRole,
    Permission,
    ReflectionVerdict,
    RiskClass,
    RunStatus,
    TaskMode,
    ToolResultStatus,
    TraceEventType,
)
from forgemind.core.errors import (
    BudgetExceededError,
    ConfigurationError,
    ForgeMindError,
    IllegalTransitionError,
    InvalidActionError,
    PermissionDeniedError,
    ProviderError,
    ToolExecutionError,
    ValidationError,
)
from forgemind.core.memory import LongTermMemoryItem, MemorySnapshot, WorkingMemory
from forgemind.core.messages import ChatMessage
from forgemind.core.plan import ExecutionPlan, PlanStep
from forgemind.core.protocols import (
    ActionSelector,
    MemoryStore,
    ModelProvider,
    Planner,
    Reflector,
    Reviewer,
    Tool,
    ToolRegistry,
)
from forgemind.core.provider import ProviderRequest, ProviderResponse
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.report import ChangedFile, EngineeringReport, TraceEvent
from forgemind.core.review import ReviewFinding, ReviewReport
from forgemind.core.state import BudgetCounters, RunState, new_run_id
from forgemind.core.task import TaskSpec
from forgemind.core.tools import (
    Observation,
    ToolCall,
    ToolManifest,
    ToolParameterSchema,
    ToolResult,
)
from forgemind.core.validation import parse_agent_action, validate_agent_action

__all__ = [
    "AbortAction",
    "ActionSelector",
    "AgentAction",
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalResponse",
    "BudgetCounters",
    "BudgetExceededError",
    "ChangedFile",
    "ChatMessage",
    "ConfigurationError",
    "EngineeringReport",
    "ExecutionPlan",
    "FindingSeverity",
    "FinishAction",
    "ForgeMindError",
    "IllegalTransitionError",
    "InvalidActionError",
    "InvokeToolAction",
    "LongTermMemoryItem",
    "MemorySnapshot",
    "MemoryStore",
    "MessageRole",
    "ModelProvider",
    "Observation",
    "Permission",
    "PermissionDeniedError",
    "PlanStep",
    "Planner",
    "ProviderError",
    "ProviderRequest",
    "ProviderResponse",
    "ReflectionSummary",
    "ReflectionVerdict",
    "Reflector",
    "RequestApprovalAction",
    "RequestReviewAction",
    "ReviewFinding",
    "ReviewReport",
    "Reviewer",
    "RevisePlanAction",
    "RiskClass",
    "RunState",
    "RunStatus",
    "RunTestsAction",
    "TaskMode",
    "TaskSpec",
    "Tool",
    "ToolCall",
    "ToolExecutionError",
    "ToolManifest",
    "ToolParameterSchema",
    "ToolRegistry",
    "ToolResult",
    "ToolResultStatus",
    "TraceEvent",
    "TraceEventType",
    "ValidationError",
    "WorkingMemory",
    "new_run_id",
    "parse_agent_action",
    "validate_agent_action",
]
