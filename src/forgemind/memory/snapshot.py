"""Budget-aware memory snapshot assembly."""

from __future__ import annotations

from forgemind.core.memory import LongTermMemoryItem, MemorySnapshot, WorkingMemory
from forgemind.memory.budget import DEFAULT_MEMORY_BUDGET, MemoryBudget
from forgemind.memory.retention import apply_retention


def build_snapshot(
    working: WorkingMemory,
    long_term: list[LongTermMemoryItem],
    *,
    budget: MemoryBudget = DEFAULT_MEMORY_BUDGET,
) -> MemorySnapshot:
    """Build a snapshot with working retention + long-term item cap applied."""

    retained = apply_retention(working, budget=budget)
    capped_long_term = long_term[: budget.max_long_term_items]
    return MemorySnapshot(working=retained, long_term=capped_long_term)
