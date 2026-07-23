"""Read-only orchestrator: drives the ASE run state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from forgemind.agent.reporting import build_engineering_report
from forgemind.agent.transitions import transition
from forgemind.config.budgets import assert_step_budget, assert_tool_budget
from forgemind.config.models import ForgeMindConfig
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
from forgemind.core.enums import ReflectionVerdict, RunStatus, TaskMode, ToolResultStatus
from forgemind.core.errors import (
    BudgetExceededError,
    IllegalTransitionError,
    InvalidActionError,
)
from forgemind.core.memory import WorkingMemory
from forgemind.core.plan import ExecutionPlan, PlanStep
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.report import EngineeringReport
from forgemind.core.state import BudgetCounters, RunState
from forgemind.core.task import TaskSpec
from forgemind.core.tools import Observation, ToolCall, ToolManifest
from forgemind.memory.store import CompositeMemoryStore, create_memory_store
from forgemind.tools.executor import ToolExecutor, observation_from_result
from forgemind.tools.repo import create_readonly_tooling


class ActionSelector(Protocol):
    async def select_action(
        self,
        state: RunState,
        memory: Any,
        *,
        available_tools: list[ToolManifest],
    ) -> AgentAction: ...


@dataclass
class RunResult:
    """Outcome of an orchestrator run."""

    state: RunState
    report: EngineeringReport | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class Orchestrator:
    """Drive one agent run through the explicit state machine.

    Phase 6 focuses on **read-only** autonomy (explain/analyze). Write/test
    actions are rejected or aborted rather than mutating the host.
    """

    def __init__(
        self,
        *,
        tools: ToolExecutor,
        memory: CompositeMemoryStore,
        actor: ActionSelector,
        readonly: bool = True,
    ) -> None:
        self._tools = tools
        self._memory = memory
        self._actor = actor
        self._readonly = readonly

    async def run(self, task: TaskSpec, *, state: RunState | None = None) -> RunResult:
        """Execute or resume a run until a terminal status is reached."""

        events: list[dict[str, Any]] = []
        if state is None:
            state = RunState(
                task=task,
                budgets=BudgetCounters(),
                status=RunStatus.RECEIVED,
            )
            await self._init_working_memory(state)
            state = transition(state, RunStatus.ANALYZING)
            events.append(_event(state, "started", {"goal": task.goal}))
            state = transition(state, RunStatus.PLANNING)
            await self._ensure_default_plan(state)
            state = transition(state, RunStatus.INVESTIGATING)
            events.append(_event(state, "investigating", {}))
        elif state.is_terminal:
            working = await self._memory.load_working(state.run_id)
            return RunResult(
                state=state,
                report=build_engineering_report(state, working),
                events=events,
            )

        finish_summary: str | None = None
        try:
            while not state.is_terminal:
                assert_step_budget(state.budgets)
                snapshot = await self._memory.snapshot(state.run_id, query=task.goal)
                manifests = self._tools.registry.list_manifests()
                action = await self._actor.select_action(
                    state,
                    snapshot,
                    available_tools=manifests,
                )
                state.budgets.steps_used += 1
                state.touch()
                events.append(
                    _event(
                        state,
                        "action",
                        {"type": action.type, "step": state.budgets.steps_used},
                    )
                )
                state, finish_summary, stop = await self._handle_action(
                    state,
                    action,
                    events,
                )
                if stop:
                    break
        except BudgetExceededError as exc:
            state.last_error = str(exc)
            state = _force_status(state, RunStatus.FAILED)
            events.append(_event(state, "budget_exceeded", {"error": str(exc)}))
        except (IllegalTransitionError, InvalidActionError) as exc:
            state.last_error = str(exc)
            state = _force_status(state, RunStatus.FAILED)
            events.append(_event(state, "error", {"error": str(exc)}))

        if state.status == RunStatus.AWAITING_APPROVAL:
            working = await self._memory.load_working(state.run_id)
            return RunResult(state=state, report=None, events=events)

        if not state.is_terminal:
            state = transition(state, RunStatus.REPORTING)
            working = await self._memory.load_working(state.run_id)
            report = build_engineering_report(
                state,
                working,
                finish_summary=finish_summary,
            )
            state = transition(state, RunStatus.COMPLETED)
            events.append(_event(state, "completed", {}))
            return RunResult(state=state, report=report, events=events)

        working = await self._memory.load_working(state.run_id)
        report = build_engineering_report(
            state,
            working,
            finish_summary=finish_summary,
        )
        return RunResult(state=state, report=report, events=events)

    async def _handle_action(
        self,
        state: RunState,
        action: AgentAction,
        events: list[dict[str, Any]],
    ) -> tuple[RunState, str | None, bool]:
        if isinstance(action, InvokeToolAction):
            return await self._handle_invoke_tool(state, action, events)
        if isinstance(action, RevisePlanAction):
            state.plan = action.plan
            working = await self._memory.load_working(state.run_id)
            working.plan = action.plan
            await self._memory.save_working(state.run_id, working)
            if state.status == RunStatus.PLANNING:
                state = transition(state, RunStatus.INVESTIGATING)
            events.append(_event(state, "plan_revised", {"reason": action.reason}))
            return state, None, False
        if isinstance(action, FinishAction):
            if state.status != RunStatus.REPORTING:
                if state.status in {RunStatus.ANALYZING, RunStatus.PLANNING}:
                    state = transition(state, RunStatus.INVESTIGATING)
                if (
                    state.status == RunStatus.REFLECTING
                    or state.status == RunStatus.REVIEWING
                    or state.status == RunStatus.INVESTIGATING
                ):
                    state = transition(state, RunStatus.REPORTING)
            target = RunStatus.COMPLETED if action.success else RunStatus.FAILED
            state = transition(state, target)
            if not action.success:
                state.last_error = action.summary
            return state, action.summary, True
        if isinstance(action, AbortAction):
            state.last_error = action.reason
            state = _force_status(state, RunStatus.ABORTED)
            return state, action.reason, True
        if isinstance(action, RequestApprovalAction):
            state = transition(state, RunStatus.AWAITING_APPROVAL)
            events.append(
                _event(
                    state,
                    "awaiting_approval",
                    {"purpose": action.purpose, "risk": action.risk_summary},
                )
            )
            return state, None, True
        if isinstance(action, RequestReviewAction):
            if state.status == RunStatus.INVESTIGATING:
                state = transition(state, RunStatus.REFLECTING)
            if state.status == RunStatus.REFLECTING or state.status != RunStatus.REVIEWING:
                state = transition(state, RunStatus.REVIEWING)
            working = await self._memory.load_working(state.run_id)
            working.reflections.append(
                ReflectionSummary(
                    verdict=ReflectionVerdict.CONTINUE,
                    helped=True,
                    learned="Self-review requested; Phase 9 reviewer not wired yet.",
                    next_hint=(
                        "Continue to report"
                        if not action.focus
                        else f"Focus: {', '.join(action.focus)}"
                    ),
                )
            )
            await self._memory.save_working(state.run_id, working)
            state = transition(state, RunStatus.REPORTING)
            return state, None, False
        if isinstance(action, RunTestsAction):
            if self._readonly:
                working = await self._memory.load_working(state.run_id)
                working.observations.append(
                    Observation(
                        source="system",
                        summary="run_tests rejected in read-only Phase 6 orchestrator",
                        details={"selector": action.selector},
                    )
                )
                await self._memory.save_working(state.run_id, working)
                return state, None, False
            state = transition(state, RunStatus.TESTING)
            return state, None, False
        raise InvalidActionError(f"unsupported action type: {type(action)!r}")

    async def _handle_invoke_tool(
        self,
        state: RunState,
        action: InvokeToolAction,
        events: list[dict[str, Any]],
    ) -> tuple[RunState, str | None, bool]:
        if self._readonly and not action.tool_name.startswith("repo."):
            working = await self._memory.load_working(state.run_id)
            working.observations.append(
                Observation(
                    source="system",
                    summary=f"Tool '{action.tool_name}' blocked in read-only mode",
                )
            )
            await self._memory.save_working(state.run_id, working)
            return state, None, False

        assert_tool_budget(state.budgets)
        call = ToolCall(
            call_id=str(uuid4()),
            tool_name=action.tool_name,
            arguments=action.arguments,
        )
        result = await self._tools.execute(call)
        state.budgets.tool_calls_used += 1
        state.touch()

        observation = observation_from_result(result)
        working = await self._memory.load_working(state.run_id)
        working.observations.append(observation)
        path = action.arguments.get("path")
        if (
            isinstance(path, str)
            and path not in working.files_inspected
            and result.status == ToolResultStatus.SUCCESS
        ):
            working.files_inspected.append(path)
        working.reflections.append(
            ReflectionSummary(
                verdict=ReflectionVerdict.CONTINUE,
                helped=result.status == ToolResultStatus.SUCCESS,
                learned=observation.summary,
            )
        )
        await self._memory.save_working(state.run_id, working)

        if state.status == RunStatus.INVESTIGATING:
            state = transition(state, RunStatus.REFLECTING)
            state = transition(state, RunStatus.INVESTIGATING)
        events.append(
            _event(
                state,
                "tool_result",
                {
                    "tool": action.tool_name,
                    "status": result.status.value,
                },
            )
        )
        return state, None, False

    async def _init_working_memory(self, state: RunState) -> None:
        memory = WorkingMemory(task_brief=state.task.goal)
        await self._memory.save_working(state.run_id, memory)

    async def _ensure_default_plan(self, state: RunState) -> None:
        if state.plan is not None:
            return
        plan = ExecutionPlan(
            summary=f"Read-only investigation for: {state.task.goal}",
            steps=[
                PlanStep(
                    id="survey",
                    title="Survey repository structure",
                    success_criteria=["Top-level layout understood"],
                ),
                PlanStep(
                    id="inspect",
                    title="Inspect relevant files",
                    success_criteria=["Key files read or searched"],
                ),
                PlanStep(
                    id="summarize",
                    title="Summarize findings",
                    success_criteria=["Engineering report produced"],
                ),
            ],
        )
        state.plan = plan
        working = await self._memory.load_working(state.run_id)
        working.plan = plan
        await self._memory.save_working(state.run_id, working)


def create_readonly_orchestrator(
    *,
    workspace_root: str | Path,
    config: ForgeMindConfig,
    actor: ActionSelector,
    memory: CompositeMemoryStore | None = None,
) -> Orchestrator:
    """Wire a read-only orchestrator with repo tools and memory."""

    tools = create_readonly_tooling(workspace_root=workspace_root, config=config)
    store = memory or create_memory_store()
    # Align run budgets from config when creating fresh runs — caller may also
    # set counters on RunState. Store config max on tools registry metadata via actor.
    return Orchestrator(tools=tools, memory=store, actor=actor, readonly=True)


def seed_budgets_from_config(config: ForgeMindConfig) -> BudgetCounters:
    """Create budget counters from config budget settings."""

    return config.budgets.to_counters()


def explain_task(workspace_root: str | Path, goal: str) -> TaskSpec:
    """Convenience TaskSpec for explain-mode runs."""

    from forgemind.core.enums import Permission

    return TaskSpec(
        goal=goal,
        workspace_root=Path(workspace_root),
        mode=TaskMode.EXPLAIN,
        permissions=[Permission.REPO_READ, Permission.GIT_READ],
    )


def _event(state: RunState, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "status": state.status.value,
        "kind": kind,
        "payload": payload,
    }


def _force_status(state: RunState, status: RunStatus) -> RunState:
    """Set a terminal/failure status even when the normal edge is awkward."""

    state.status = status
    state.touch()
    return state
