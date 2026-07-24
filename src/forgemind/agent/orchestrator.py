"""Read-only orchestrator: drives the ASE run state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from forgemind.agent.reporting import build_engineering_report
from forgemind.agent.transitions import transition
from forgemind.config.budgets import (
    assert_repair_budget,
    assert_step_budget,
    assert_tool_budget,
)
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
from forgemind.core.plan import ExecutionPlan
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.report import EngineeringReport
from forgemind.core.state import BudgetCounters, RunState
from forgemind.core.task import TaskSpec
from forgemind.core.tools import Observation, ToolCall, ToolManifest
from forgemind.memory.store import CompositeMemoryStore, create_memory_store
from forgemind.planning import HeuristicPlanner
from forgemind.reflection import HeuristicReflector, should_revise_plan
from forgemind.tools.executor import ToolExecutor, observation_from_result
from forgemind.tools.repo import create_readonly_tooling, create_standard_tooling

_READONLY_TOOLS = frozenset(
    {
        "repo.list_structure",
        "repo.search",
        "repo.read_file",
    }
)
_WRITE_TOOLS = frozenset({"repo.write_file", "repo.edit_file"})
_TEST_TOOLS = frozenset({"test.run"})


class ActionSelector(Protocol):
    async def select_action(
        self,
        state: RunState,
        memory: Any,
        *,
        available_tools: list[ToolManifest],
    ) -> AgentAction: ...


class PlannerPort(Protocol):
    async def create_plan(self, state: RunState, memory: Any) -> ExecutionPlan: ...

    async def revise_plan(
        self,
        state: RunState,
        memory: Any,
        *,
        reason: str,
    ) -> ExecutionPlan: ...


class ReflectorPort(Protocol):
    async def reflect(
        self,
        state: RunState,
        memory: Any,
        *,
        observation: Observation,
    ) -> ReflectionSummary: ...


@dataclass
class RunResult:
    """Outcome of an orchestrator run."""

    state: RunState
    report: EngineeringReport | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class Orchestrator:
    """Drive one agent run through the explicit state machine.

    Read-only mode (default) allows survey/read tools only.
    Mutable mode (Phase 8) enables write/edit tools and the test-repair loop.
    """

    def __init__(
        self,
        *,
        tools: ToolExecutor,
        memory: CompositeMemoryStore,
        actor: ActionSelector,
        planner: PlannerPort | None = None,
        reflector: ReflectorPort | None = None,
        readonly: bool = True,
        default_budgets: BudgetCounters | None = None,
    ) -> None:
        self._tools = tools
        self._memory = memory
        self._actor = actor
        self._planner: PlannerPort = planner or HeuristicPlanner()
        self._reflector: ReflectorPort = reflector or HeuristicReflector()
        self._readonly = readonly
        self._default_budgets = default_budgets

    async def run(self, task: TaskSpec, *, state: RunState | None = None) -> RunResult:
        """Execute or resume a run until a terminal status is reached."""

        events: list[dict[str, Any]] = []
        if state is None:
            budgets = (
                self._default_budgets.model_copy(deep=True)
                if self._default_budgets is not None
                else BudgetCounters()
            )
            state = RunState(
                task=task,
                budgets=budgets,
                status=RunStatus.RECEIVED,
            )
            await self._init_working_memory(state)
            state = transition(state, RunStatus.ANALYZING)
            events.append(_event(state, "started", {"goal": task.goal}))
            state = transition(state, RunStatus.PLANNING)
            await self._create_initial_plan(state)
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
                if state.status in {RunStatus.ACTING, RunStatus.TESTING}:
                    state = transition(state, RunStatus.REFLECTING)
                if state.status in {
                    RunStatus.REFLECTING,
                    RunStatus.REVIEWING,
                    RunStatus.INVESTIGATING,
                }:
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
                        summary="run_tests rejected in read-only orchestrator",
                        details={"selector": action.selector},
                    )
                )
                await self._memory.save_working(state.run_id, working)
                return state, None, False
            return await self._handle_run_tests(state, action, events)
        raise InvalidActionError(f"unsupported action type: {type(action)!r}")

    async def _handle_invoke_tool(
        self,
        state: RunState,
        action: InvokeToolAction,
        events: list[dict[str, Any]],
    ) -> tuple[RunState, str | None, bool]:
        if self._readonly and action.tool_name not in _READONLY_TOOLS:
            working = await self._memory.load_working(state.run_id)
            working.observations.append(
                Observation(
                    source="system",
                    summary=f"Tool '{action.tool_name}' blocked in read-only mode",
                )
            )
            await self._memory.save_working(state.run_id, working)
            return state, None, False

        if action.tool_name in _TEST_TOOLS:
            # Prefer RunTestsAction, but allow direct invoke_tool for test.run.
            return await self._handle_run_tests(
                state,
                RunTestsAction(selector=action.arguments.get("selector")),
                events,
            )

        assert_tool_budget(state.budgets)
        if action.tool_name in _WRITE_TOOLS and state.status == RunStatus.INVESTIGATING:
            state = transition(state, RunStatus.ACTING)

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
        await self._memory.save_working(state.run_id, working)

        # Hard deny on write path (denylist / missing permission) ends the loop.
        if (
            action.tool_name in _WRITE_TOOLS
            and result.status == ToolResultStatus.DENIED
        ):
            state.last_error = result.error or observation.summary
            events.append(
                _event(
                    state,
                    "tool_result",
                    {"tool": action.tool_name, "status": result.status.value},
                )
            )
            state = _force_status(state, RunStatus.FAILED)
            return state, None, True

        resume_as = (
            RunStatus.ACTING
            if action.tool_name in _WRITE_TOOLS
            else RunStatus.INVESTIGATING
        )
        return await self._after_tool(
            state,
            action.tool_name,
            result.status,
            observation,
            events,
            resume_as=resume_as,
        )

    async def _handle_run_tests(
        self,
        state: RunState,
        action: RunTestsAction,
        events: list[dict[str, Any]],
    ) -> tuple[RunState, str | None, bool]:
        if state.status in {RunStatus.INVESTIGATING, RunStatus.ACTING, RunStatus.REFLECTING}:
            state = transition(state, RunStatus.TESTING)

        assert_tool_budget(state.budgets)
        args: dict[str, Any] = {}
        if isinstance(action.selector, str) and action.selector:
            args["selector"] = action.selector
        call = ToolCall(
            call_id=str(uuid4()),
            tool_name="test.run",
            arguments=args,
        )
        result = await self._tools.execute(call)
        state.budgets.tool_calls_used += 1
        state.touch()

        observation = observation_from_result(result)
        working = await self._memory.load_working(state.run_id)
        working.observations.append(observation)
        passed = (
            isinstance(result.output, dict)
            and bool(result.output.get("passed"))
            and result.status == ToolResultStatus.SUCCESS
        )
        working.test_summaries.append("tests passed" if passed else "tests failed")
        await self._memory.save_working(state.run_id, working)

        events.append(
            _event(
                state,
                "test_result",
                {"passed": passed, "status": result.status.value},
            )
        )

        if result.status == ToolResultStatus.DENIED:
            state.last_error = result.error or observation.summary
            state = _force_status(state, RunStatus.FAILED)
            return state, None, True

        if not passed:
            try:
                assert_repair_budget(state.budgets)
            except BudgetExceededError as exc:
                state.last_error = str(exc)
                state = _force_status(state, RunStatus.FAILED)
                return state, None, True
            state.budgets.repair_iterations_used += 1

        resume_as = RunStatus.INVESTIGATING if passed else RunStatus.ACTING
        return await self._after_tool(
            state,
            "test.run",
            result.status,
            observation,
            events,
            resume_as=resume_as,
        )

    async def _after_tool(
        self,
        state: RunState,
        tool_name: str,
        status: ToolResultStatus,
        observation: Observation,
        events: list[dict[str, Any]],
        *,
        resume_as: RunStatus = RunStatus.INVESTIGATING,
    ) -> tuple[RunState, str | None, bool]:
        if can_go_reflecting(state.status):
            state = transition(state, RunStatus.REFLECTING)

        snapshot = await self._memory.snapshot(state.run_id, query=state.task.goal)
        reflection = await self._reflector.reflect(
            state,
            snapshot,
            observation=observation,
        )
        working = await self._memory.load_working(state.run_id)
        working.reflections.append(reflection)
        await self._memory.save_working(state.run_id, working)
        events.append(
            _event(
                state,
                "reflection",
                {
                    "verdict": reflection.verdict.value,
                    "helped": reflection.helped,
                },
            )
        )

        if should_revise_plan(reflection):
            reason = reflection.plan_adjustment or reflection.learned
            snapshot = await self._memory.snapshot(state.run_id, query=state.task.goal)
            revised = await self._planner.revise_plan(state, snapshot, reason=reason)
            state.plan = revised
            working = await self._memory.load_working(state.run_id)
            working.plan = revised
            await self._memory.save_working(state.run_id, working)
            events.append(_event(state, "plan_revised", {"reason": reason}))

        if state.status == RunStatus.REFLECTING:
            state = transition(state, resume_as)
        events.append(
            _event(
                state,
                "tool_result",
                {
                    "tool": tool_name,
                    "status": status.value,
                },
            )
        )
        return state, None, False

    async def _init_working_memory(self, state: RunState) -> None:
        memory = WorkingMemory(task_brief=state.task.goal)
        await self._memory.save_working(state.run_id, memory)

    async def _create_initial_plan(self, state: RunState) -> None:
        if state.plan is not None:
            return
        snapshot = await self._memory.snapshot(state.run_id, query=state.task.goal)
        plan = await self._planner.create_plan(state, snapshot)
        state.plan = plan
        working = await self._memory.load_working(state.run_id)
        working.plan = plan
        await self._memory.save_working(state.run_id, working)
        state.current_step_id = plan.steps[0].id if plan.steps else None


def can_go_reflecting(status: RunStatus) -> bool:
    """Return True if ``status`` may transition into reflecting."""

    return status in {
        RunStatus.INVESTIGATING,
        RunStatus.ACTING,
        RunStatus.TESTING,
    }


def create_readonly_orchestrator(
    *,
    workspace_root: str | Path,
    config: ForgeMindConfig,
    actor: ActionSelector,
    memory: CompositeMemoryStore | None = None,
    planner: PlannerPort | None = None,
    reflector: ReflectorPort | None = None,
) -> Orchestrator:
    """Wire a read-only orchestrator with repo tools, memory, planner, and reflector."""

    tools = create_readonly_tooling(workspace_root=workspace_root, config=config)
    store = memory or create_memory_store()
    return Orchestrator(
        tools=tools,
        memory=store,
        actor=actor,
        planner=planner,
        reflector=reflector,
        readonly=True,
        default_budgets=seed_budgets_from_config(config),
    )


def create_mutable_orchestrator(
    *,
    workspace_root: str | Path,
    config: ForgeMindConfig,
    actor: ActionSelector,
    memory: CompositeMemoryStore | None = None,
    planner: PlannerPort | None = None,
    reflector: ReflectorPort | None = None,
) -> Orchestrator:
    """Wire a mutable orchestrator with read/write/test tools (Phase 8)."""

    tools = create_standard_tooling(workspace_root=workspace_root, config=config)
    store = memory or create_memory_store()
    return Orchestrator(
        tools=tools,
        memory=store,
        actor=actor,
        planner=planner,
        reflector=reflector,
        readonly=False,
        default_budgets=seed_budgets_from_config(config),
    )


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


def fix_task(workspace_root: str | Path, goal: str) -> TaskSpec:
    """Convenience TaskSpec for fix-mode runs with write/test permissions."""

    from forgemind.core.enums import Permission

    return TaskSpec(
        goal=goal,
        workspace_root=Path(workspace_root),
        mode=TaskMode.FIX,
        permissions=[
            Permission.REPO_READ,
            Permission.REPO_WRITE,
            Permission.TEST_RUN,
            Permission.GIT_READ,
        ],
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
