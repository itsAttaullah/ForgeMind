"""Orchestrator end-to-end tests (read-only Phase 6)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from forgemind.agent import (
    Orchestrator,
    ProviderActionSelector,
    ScriptedActionSelector,
    create_readonly_orchestrator,
    explain_task,
    seed_budgets_from_config,
)
from forgemind.config import AgentProfile, profile_config
from forgemind.core.enums import RunStatus
from forgemind.core.state import RunState
from forgemind.memory import create_memory_store
from forgemind.providers import StubProvider

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "sample_repo"


def test_scripted_readonly_explain_run() -> None:
    config = profile_config(AgentProfile.READONLY)
    actor = ScriptedActionSelector(
        [
            {
                "type": "invoke_tool",
                "tool_name": "repo.list_structure",
                "arguments": {"path": ".", "max_depth": 2},
            },
            {
                "type": "invoke_tool",
                "tool_name": "repo.read_file",
                "arguments": {"path": "README.md"},
            },
            {
                "type": "finish",
                "summary": "Sample repo contains README and src/app.py",
                "success": True,
            },
        ]
    )
    orch = create_readonly_orchestrator(
        workspace_root=FIXTURE_ROOT,
        config=config,
        actor=actor,
    )
    task = explain_task(FIXTURE_ROOT, "Explain this repository")
    result = asyncio.run(orch.run(task))
    assert result.state.status == RunStatus.COMPLETED
    assert result.report is not None
    assert result.report.status == RunStatus.COMPLETED
    assert result.state.budgets.tool_calls_used >= 2
    assert result.state.budgets.steps_used >= 3


def test_runstate_resume_smoke() -> None:
    config = profile_config(AgentProfile.READONLY)
    memory = create_memory_store()
    actor = ScriptedActionSelector(
        [
            {
                "type": "invoke_tool",
                "tool_name": "repo.search",
                "arguments": {"query": "JWT_AUTH_MARKER"},
            },
            {
                "type": "finish",
                "summary": "Found JWT marker in README",
                "success": True,
            },
        ]
    )
    orch = create_readonly_orchestrator(
        workspace_root=FIXTURE_ROOT,
        config=config,
        actor=actor,
        memory=memory,
    )
    task = explain_task(FIXTURE_ROOT, "Find JWT marker")

    async def _run() -> None:
        first = await orch.run(task)
        assert first.state.status == RunStatus.COMPLETED
        restored = RunState.model_validate(first.state.model_dump(mode="json"))
        resumed = await orch.run(task, state=restored)
        assert resumed.state.status == RunStatus.COMPLETED
        assert resumed.state.run_id == first.state.run_id
        assert resumed.report is not None

    asyncio.run(_run())


def test_stub_provider_actor_e2e() -> None:
    config = profile_config(AgentProfile.READONLY)
    provider = StubProvider(
        responses=[
            json.dumps(
                {
                    "type": "invoke_tool",
                    "tool_name": "repo.list_structure",
                    "arguments": {"path": "."},
                }
            ),
            json.dumps(
                {
                    "type": "finish",
                    "summary": "Repository surveyed via stub provider",
                    "success": True,
                }
            ),
        ]
    )
    orch = create_readonly_orchestrator(
        workspace_root=FIXTURE_ROOT,
        config=config,
        actor=ProviderActionSelector(provider),
    )
    result = asyncio.run(orch.run(explain_task(FIXTURE_ROOT, "Survey the repo")))
    assert result.state.status == RunStatus.COMPLETED
    assert result.report is not None
    assert result.report.key_findings


def test_readonly_blocks_non_repo_tool() -> None:
    config = profile_config(AgentProfile.READONLY)
    actor = ScriptedActionSelector(
        [
            {"type": "invoke_tool", "tool_name": "shell.exec", "arguments": {}},
            {"type": "finish", "summary": "Blocked shell and finished", "success": True},
        ]
    )
    orch = create_readonly_orchestrator(
        workspace_root=FIXTURE_ROOT,
        config=config,
        actor=actor,
    )
    result = asyncio.run(orch.run(explain_task(FIXTURE_ROOT, "Try shell")))
    assert result.state.status == RunStatus.COMPLETED
    assert result.state.budgets.tool_calls_used == 0


def test_budget_exhaustion_fails() -> None:
    config = profile_config(AgentProfile.READONLY)
    actor = ScriptedActionSelector(
        [
            {
                "type": "invoke_tool",
                "tool_name": "repo.list_structure",
                "arguments": {"path": "."},
            }
            for _ in range(5)
        ]
    )
    base = create_readonly_orchestrator(
        workspace_root=FIXTURE_ROOT,
        config=config,
        actor=actor,
    )
    task = explain_task(FIXTURE_ROOT, "Loop until budget")
    orch = Orchestrator(
        tools=base._tools,
        memory=base._memory,
        actor=actor,
        readonly=True,
    )

    async def _run() -> None:
        warm = RunState(
            task=task,
            budgets=seed_budgets_from_config(config).model_copy(
                update={"max_steps": 1, "steps_used": 0}
            ),
            status=RunStatus.INVESTIGATING,
        )
        await orch._init_working_memory(warm)
        await orch._create_initial_plan(warm)
        result = await orch.run(task, state=warm)
        assert result.state.status == RunStatus.FAILED
        assert result.state.last_error is not None
        assert "budget" in result.state.last_error.lower()

    asyncio.run(_run())
