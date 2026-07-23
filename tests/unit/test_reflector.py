"""Reflector unit tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from forgemind.core.enums import ReflectionVerdict, TaskMode
from forgemind.core.memory import MemorySnapshot, WorkingMemory
from forgemind.core.state import RunState
from forgemind.core.task import TaskSpec
from forgemind.core.tools import Observation
from forgemind.memory import create_memory_store
from forgemind.providers import StubProvider
from forgemind.reflection import (
    HeuristicReflector,
    ProviderReflector,
    should_revise_plan,
)


def _state() -> RunState:
    return RunState(
        task=TaskSpec(
            goal="Explain repo",
            workspace_root=Path("."),
            mode=TaskMode.EXPLAIN,
        )
    )


def test_heuristic_reflect_continue_on_success() -> None:
    reflector = HeuristicReflector()
    observation = Observation(source="tool:repo.search", summary="Found matches")
    summary = asyncio.run(reflector.reflect(_state(), MemorySnapshot(), observation=observation))
    assert summary.verdict == ReflectionVerdict.CONTINUE
    assert summary.helped is True
    assert "chain_of_thought" not in summary.metadata


def test_heuristic_reflect_revise_on_denied() -> None:
    reflector = HeuristicReflector()
    observation = Observation(
        source="tool:repo.read_file",
        summary="repo.read_file denied: path denied by denylist",
    )
    summary = asyncio.run(reflector.reflect(_state(), MemorySnapshot(), observation=observation))
    assert should_revise_plan(summary)
    assert summary.plan_adjustment is not None


def test_provider_reflector_sanitizes_cot_metadata() -> None:
    payload = {
        "verdict": "continue",
        "helped": True,
        "learned": "Useful file found",
        "plan_adjustment": None,
        "next_hint": "Read more",
        "metadata": {"chain_of_thought": "PRIVATE", "reflector": "provider"},
    }
    reflector = ProviderReflector(StubProvider(responses=[json.dumps(payload)]))
    summary = asyncio.run(
        reflector.reflect(
            _state(),
            MemorySnapshot(),
            observation=Observation(source="tool:repo.read_file", summary="ok"),
        )
    )
    assert summary.learned == "Useful file found"
    assert "chain_of_thought" not in summary.metadata


def test_memory_store_keeps_summary_only_reflections() -> None:
    store = create_memory_store()

    async def _run() -> None:
        reflector = HeuristicReflector()
        summary = await reflector.reflect(
            _state(),
            MemorySnapshot(
                working=WorkingMemory(
                    observations=[
                        Observation(source="tool:x", summary="denied once"),
                        Observation(source="tool:x", summary="denied twice"),
                        Observation(source="tool:x", summary="denied thrice"),
                    ]
                )
            ),
            observation=Observation(source="tool:x", summary="denied again"),
        )
        assert should_revise_plan(summary)
        memory = WorkingMemory(reflections=[summary])
        await store.save_working("r1", memory)
        loaded = await store.load_working("r1")
        assert loaded.reflections[0].learned
        assert "chain_of_thought" not in loaded.reflections[0].metadata

    asyncio.run(_run())
