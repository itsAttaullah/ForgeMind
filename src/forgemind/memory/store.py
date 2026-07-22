"""Composite MemoryStore implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from forgemind.core.memory import LongTermMemoryItem, MemorySnapshot, WorkingMemory
from forgemind.memory.budget import DEFAULT_MEMORY_BUDGET, MemoryBudget
from forgemind.memory.long_term import InMemoryLongTermStore, JsonFileLongTermStore
from forgemind.memory.snapshot import build_snapshot
from forgemind.memory.working import InMemoryWorkingStore, JsonFileWorkingStore


class WorkingStore(Protocol):
    async def load(self, run_id: str) -> WorkingMemory: ...

    async def save(self, run_id: str, memory: WorkingMemory) -> None: ...


class LongTermStore(Protocol):
    async def retrieve(self, query: str, *, limit: int = 5) -> list[LongTermMemoryItem]: ...

    async def upsert(self, item: LongTermMemoryItem) -> LongTermMemoryItem: ...


class CompositeMemoryStore:
    """Combines working + long-term backends behind the ``MemoryStore`` port."""

    def __init__(
        self,
        working: WorkingStore,
        long_term: LongTermStore,
        *,
        budget: MemoryBudget = DEFAULT_MEMORY_BUDGET,
    ) -> None:
        self._working = working
        self._long_term = long_term
        self._budget = budget

    async def load_working(self, run_id: str) -> WorkingMemory:
        return await self._working.load(run_id)

    async def save_working(self, run_id: str, memory: WorkingMemory) -> None:
        await self._working.save(run_id, memory)

    async def retrieve_long_term(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[LongTermMemoryItem]:
        capped = min(limit, self._budget.max_long_term_items)
        if capped <= 0:
            return []
        return await self._long_term.retrieve(query, limit=capped)

    async def snapshot(self, run_id: str, *, query: str | None = None) -> MemorySnapshot:
        working = await self.load_working(run_id)
        long_term: list[LongTermMemoryItem] = []
        if query:
            long_term = await self.retrieve_long_term(
                query,
                limit=self._budget.max_long_term_items,
            )
        return build_snapshot(working, long_term, budget=self._budget)

    async def remember(self, item: LongTermMemoryItem) -> LongTermMemoryItem:
        """Upsert a summarized long-term item (never private CoT)."""

        return await self._long_term.upsert(item)


def create_memory_store(
    *,
    budget: MemoryBudget | None = None,
    working_dir: str | Path | None = None,
    long_term_path: str | Path | None = None,
) -> CompositeMemoryStore:
    """Create an in-memory or JSON-backed composite memory store.

    If ``working_dir`` / ``long_term_path`` are omitted, pure in-memory backends
    are used (ideal for unit tests).
    """

    resolved_budget = budget or DEFAULT_MEMORY_BUDGET
    working: WorkingStore
    long_term: LongTermStore

    if working_dir is None:
        working = InMemoryWorkingStore(budget=resolved_budget)
    else:
        working = JsonFileWorkingStore(working_dir, budget=resolved_budget)

    if long_term_path is None:
        long_term = InMemoryLongTermStore()
    else:
        long_term = JsonFileLongTermStore(long_term_path)

    return CompositeMemoryStore(working, long_term, budget=resolved_budget)
