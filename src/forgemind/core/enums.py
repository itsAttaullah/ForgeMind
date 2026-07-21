"""Shared enumerations for ForgeMind domain types."""

from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    """Lifecycle states for an ``AgentRun`` (ADR 0003)."""

    RECEIVED = "received"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    INVESTIGATING = "investigating"
    ACTING = "acting"
    REFLECTING = "reflecting"
    TESTING = "testing"
    REVIEWING = "reviewing"
    AWAITING_APPROVAL = "awaiting_approval"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class TaskMode(StrEnum):
    """High-level operating mode for a task."""

    EXPLAIN = "explain"
    FIX = "fix"
    FEATURE = "feature"
    REVIEW = "review"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


class RiskClass(StrEnum):
    """Risk classification for tools and actions (ADR 0005)."""

    READ = "read"
    WRITE = "write"
    EXEC = "exec"
    MUTATE_GIT = "mutate_git"
    MUTATE_REMOTE = "mutate_remote"


class Permission(StrEnum):
    """Capability tokens granted to a run."""

    REPO_READ = "repo.read"
    REPO_WRITE = "repo.write"
    TEST_RUN = "test.run"
    GIT_READ = "git.read"
    GIT_WRITE = "git.write"
    GITHUB_READ = "github.read"
    GITHUB_WRITE = "github.write"
    NETWORK_EGRESS = "network.egress"


class MessageRole(StrEnum):
    """Roles for provider chat messages."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolResultStatus(StrEnum):
    """Outcome status for a tool invocation."""

    SUCCESS = "success"
    ERROR = "error"
    DENIED = "denied"
    TIMEOUT = "timeout"


class ReflectionVerdict(StrEnum):
    """High-level reflector recommendation (summary only)."""

    CONTINUE = "continue"
    RETRY = "retry"
    REVISE_PLAN = "revise_plan"
    ESCALATE = "escalate"
    STOP = "stop"


class FindingSeverity(StrEnum):
    """Severity for review findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalDecision(StrEnum):
    """Human (or policy) decision on an approval request."""

    APPROVED = "approved"
    DENIED = "denied"
    DEFERRED = "deferred"


class TraceEventType(StrEnum):
    """Categories for observability events."""

    RUN_STARTED = "run_started"
    STATE_CHANGED = "state_changed"
    ACTION_SELECTED = "action_selected"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    REFLECTION = "reflection"
    APPROVAL = "approval"
    REVIEW = "review"
    ERROR = "error"
    RUN_FINISHED = "run_finished"
