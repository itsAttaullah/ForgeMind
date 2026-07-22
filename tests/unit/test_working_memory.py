"""Working memory retention and persistence tests."""

from __future__ import annotations

import asyncio

from forgemind.core.enums import ReflectionVerdict
from forgemind.core.memory import WorkingMemory
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.tools import Observation
from forgemind.memory import (
    InMemoryWorkingStore,
    JsonFileWorkingStore,
    MemoryBudget,
    apply_retention,
    sanitize_metadata,
    sanitize_reflection,
)


def test_sanitize_metadata_strips_cot_keys() -> None:
    cleaned = sanitize_metadata(
        {"ok": "yes", "chain_of_thought": "secret", "CoT": "nope", "score": 1}
    )
    assert cleaned == {"ok": "yes", "score": 1}


def test_apply_retention_keeps_recent_only() -> None:
    budget = MemoryBudget(max_observations=2, max_reflections=1)
    memory = WorkingMemory(
        observations=[
            Observation(source="tool:a", summary="one"),
            Observation(source="tool:b", summary="two"),
            Observation(source="tool:c", summary="three"),
        ],
        reflections=[
            ReflectionSummary(
                verdict=ReflectionVerdict.CONTINUE,
                helped=True,
                learned="old",
            ),
            ReflectionSummary(
                verdict=ReflectionVerdict.CONTINUE,
                helped=True,
                learned="new",
                metadata={"private_cot": "hidden"},
            ),
        ],
    )
    retained = apply_retention(memory, budget=budget)
    assert [item.summary for item in retained.observations] == ["two", "three"]
    assert len(retained.reflections) == 1
    assert retained.reflections[0].learned == "new"
    assert "private_cot" not in retained.reflections[0].metadata


def test_sanitize_reflection_truncates_learned() -> None:
    budget = MemoryBudget(max_reflection_learned_chars=10)
    reflection = ReflectionSummary(
        verdict=ReflectionVerdict.CONTINUE,
        helped=True,
        learned="abcdefghijklmnopqrstuvwxyz",
    )
    cleaned = sanitize_reflection(reflection, budget=budget)
    assert cleaned.learned.endswith("...")
    assert len(cleaned.learned) == 10


def test_in_memory_working_store_round_trip() -> None:
    store = InMemoryWorkingStore(budget=MemoryBudget(max_observations=10))

    async def _run() -> None:
        await store.append_observation(
            "run-1",
            Observation(source="tool:repo.search", summary="found jwt"),
        )
        await store.append_reflection(
            "run-1",
            ReflectionSummary(
                verdict=ReflectionVerdict.CONTINUE,
                helped=True,
                learned="Auth module exists",
                metadata={"chain_of_thought": "should not persist"},
            ),
        )
        memory = await store.load("run-1")
        assert len(memory.observations) == 1
        assert memory.reflections[0].learned == "Auth module exists"
        assert "chain_of_thought" not in memory.reflections[0].metadata

    asyncio.run(_run())


def test_json_working_store_persists(tmp_path) -> None:
    store = JsonFileWorkingStore(tmp_path / "working")

    async def _run() -> None:
        memory = WorkingMemory(task_brief="Add JWT")
        await store.save("abc", memory)
        loaded = await store.load("abc")
        assert loaded.task_brief == "Add JWT"
        assert (tmp_path / "working" / "abc.json").is_file()

    asyncio.run(_run())
