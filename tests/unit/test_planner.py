"""Planner unit tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from forgemind.core.enums import TaskMode
from forgemind.core.memory import MemorySnapshot, WorkingMemory
from forgemind.core.state import RunState
from forgemind.core.task import TaskSpec
from forgemind.core.tools import Observation
from forgemind.planning import HeuristicPlanner, ProviderPlanner
from forgemind.providers import StubProvider


def _state(mode: TaskMode = TaskMode.EXPLAIN) -> RunState:
    return RunState(
        task=TaskSpec(
            goal="Explain authentication flow",
            workspace_root=Path("."),
            mode=mode,
        )
    )


def test_heuristic_planner_creates_explain_plan() -> None:
    planner = HeuristicPlanner()
    plan = asyncio.run(planner.create_plan(_state(), MemorySnapshot()))
    assert plan.steps
    assert plan.steps[0].id == "survey"
    assert "Explain" in plan.summary


def test_heuristic_revise_appends_step() -> None:
    planner = HeuristicPlanner()
    state = _state()
    memory = MemorySnapshot(
        working=WorkingMemory(
            files_inspected=["README.md"],
            observations=[Observation(source="tool:repo.read_file", summary="Read README")],
        )
    )

    async def _run() -> None:
        state.plan = await planner.create_plan(state, memory)
        original_count = len(state.plan.steps)
        revised = await planner.revise_plan(
            state,
            memory,
            reason="Need to inspect auth package",
        )
        assert len(revised.steps) == original_count + 1
        assert revised.metadata.get("revision_count") == 1
        assert "Need to inspect auth package" in revised.open_questions

    asyncio.run(_run())


def test_provider_planner_parses_json() -> None:
    payload = {
        "summary": "Provider plan",
        "steps": [
            {
                "id": "one",
                "title": "Step one",
                "success_criteria": ["done"],
            }
        ],
        "risks": [],
        "open_questions": [],
    }
    provider = StubProvider(responses=[json.dumps(payload)])
    planner = ProviderPlanner(provider)
    plan = asyncio.run(planner.create_plan(_state(), MemorySnapshot()))
    assert plan.summary == "Provider plan"
    assert plan.steps[0].id == "one"
