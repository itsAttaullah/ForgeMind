"""Long-term memory and composite store tests."""

from __future__ import annotations

import asyncio

from forgemind.core.enums import ReflectionVerdict
from forgemind.core.memory import LongTermMemoryItem, WorkingMemory
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.tools import Observation
from forgemind.memory import (
    CompositeMemoryStore,
    InMemoryLongTermStore,
    InMemoryWorkingStore,
    JsonFileLongTermStore,
    MemoryBudget,
    create_memory_store,
    score_item,
)


def test_score_and_retrieve_long_term() -> None:
    store = InMemoryLongTermStore()

    async def _run() -> None:
        await store.upsert(
            LongTermMemoryItem(
                key="jwt-strategy",
                content="Prefer extending existing auth with JWT middleware",
                kind="strategy",
            )
        )
        await store.upsert(
            LongTermMemoryItem(
                key="pytest-tip",
                content="Use fixture repos for agent tool tests",
                kind="fact",
            )
        )
        hits = await store.retrieve("JWT authentication middleware", limit=2)
        assert hits
        assert hits[0].key == "jwt-strategy"
        assert hits[0].score is not None and hits[0].score > 0

    asyncio.run(_run())


def test_json_long_term_persists(tmp_path) -> None:
    path = tmp_path / "ltm.json"

    async def _run() -> None:
        store = JsonFileLongTermStore(path)
        await store.upsert(LongTermMemoryItem(key="k1", content="repo uses hatchling", kind="fact"))
        reloaded = JsonFileLongTermStore(path)
        item = await reloaded.get("k1")
        assert item is not None
        assert "hatchling" in item.content

    asyncio.run(_run())


def test_composite_snapshot_budget() -> None:
    budget = MemoryBudget(max_observations=2, max_long_term_items=1)
    working = InMemoryWorkingStore(budget=budget)
    long_term = InMemoryLongTermStore()
    store = CompositeMemoryStore(working, long_term, budget=budget)

    async def _run() -> None:
        await long_term.upsert(
            LongTermMemoryItem(key="auth", content="JWT auth pattern", kind="strategy")
        )
        await long_term.upsert(
            LongTermMemoryItem(key="other", content="unrelated note", kind="fact")
        )
        for summary in ("a", "b", "c"):
            memory = await working.load("r1")
            memory.observations.append(Observation(source="tool:x", summary=summary))
            await working.save("r1", memory)

        snap = await store.snapshot("r1", query="JWT auth")
        assert len(snap.working.observations) == 2
        assert [item.summary for item in snap.working.observations] == ["b", "c"]
        assert len(snap.long_term) == 1
        assert snap.long_term[0].key == "auth"

    asyncio.run(_run())


def test_create_memory_store_factory(tmp_path) -> None:
    store = create_memory_store(
        working_dir=tmp_path / "w",
        long_term_path=tmp_path / "ltm.json",
    )

    async def _run() -> None:
        await store.save_working("run", WorkingMemory(task_brief="demo"))
        await store.remember(LongTermMemoryItem(key="demo", content="demo fact", kind="fact"))
        loaded = await store.load_working("run")
        assert loaded.task_brief == "demo"
        hits = await store.retrieve_long_term("demo", limit=3)
        assert hits[0].key == "demo"

    asyncio.run(_run())


def test_score_item_empty_query() -> None:
    item = LongTermMemoryItem(key="k", content="hello world", kind="fact")
    assert score_item("", item) == 0.0


def test_reflection_only_summaries_in_snapshot() -> None:
    store = create_memory_store()

    async def _run() -> None:
        memory = WorkingMemory(
            reflections=[
                ReflectionSummary(
                    verdict=ReflectionVerdict.CONTINUE,
                    helped=True,
                    learned="Use existing auth package",
                    metadata={"chain_of_thought": "PRIVATE"},
                )
            ]
        )
        await store.save_working("r", memory)
        snap = await store.snapshot("r")
        assert snap.working.reflections[0].learned == "Use existing auth package"
        assert "chain_of_thought" not in snap.working.reflections[0].metadata

    asyncio.run(_run())
