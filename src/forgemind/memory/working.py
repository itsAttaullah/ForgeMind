"""Working-memory stores (in-memory + JSON file persistence)."""

from __future__ import annotations

import json
from pathlib import Path

from forgemind.core.memory import WorkingMemory
from forgemind.core.plan import ExecutionPlan
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.tools import Observation
from forgemind.memory.budget import DEFAULT_MEMORY_BUDGET, MemoryBudget
from forgemind.memory.retention import apply_retention, sanitize_observation, sanitize_reflection


class InMemoryWorkingStore:
    """Process-local working memory keyed by ``run_id``."""

    def __init__(self, *, budget: MemoryBudget = DEFAULT_MEMORY_BUDGET) -> None:
        self._budget = budget
        self._data: dict[str, WorkingMemory] = {}

    async def load(self, run_id: str) -> WorkingMemory:
        memory = self._data.get(run_id)
        if memory is None:
            return WorkingMemory()
        return memory.model_copy(deep=True)

    async def save(self, run_id: str, memory: WorkingMemory) -> None:
        self._data[run_id] = apply_retention(memory, budget=self._budget)

    async def clear(self, run_id: str) -> None:
        self._data.pop(run_id, None)

    async def append_observation(self, run_id: str, observation: Observation) -> WorkingMemory:
        memory = await self.load(run_id)
        memory.observations.append(sanitize_observation(observation, budget=self._budget))
        await self.save(run_id, memory)
        return await self.load(run_id)

    async def append_reflection(
        self,
        run_id: str,
        reflection: ReflectionSummary,
    ) -> WorkingMemory:
        memory = await self.load(run_id)
        memory.reflections.append(sanitize_reflection(reflection, budget=self._budget))
        await self.save(run_id, memory)
        return await self.load(run_id)

    async def set_plan(self, run_id: str, plan: ExecutionPlan | None) -> WorkingMemory:
        memory = await self.load(run_id)
        memory.plan = plan
        await self.save(run_id, memory)
        return await self.load(run_id)

    async def note_file(self, run_id: str, path: str) -> WorkingMemory:
        memory = await self.load(run_id)
        if path not in memory.files_inspected:
            memory.files_inspected.append(path)
        await self.save(run_id, memory)
        return await self.load(run_id)


class JsonFileWorkingStore:
    """Persist working memory as one JSON file per run under a directory."""

    def __init__(
        self,
        directory: str | Path,
        *,
        budget: MemoryBudget = DEFAULT_MEMORY_BUDGET,
    ) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)
        self._budget = budget

    def _path_for(self, run_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)
        return self._directory / f"{safe}.json"

    async def load(self, run_id: str) -> WorkingMemory:
        path = self._path_for(run_id)
        if not path.is_file():
            return WorkingMemory()
        raw = json.loads(path.read_text(encoding="utf-8"))
        return WorkingMemory.model_validate(raw)

    async def save(self, run_id: str, memory: WorkingMemory) -> None:
        retained = apply_retention(memory, budget=self._budget)
        path = self._path_for(run_id)
        path.write_text(
            json.dumps(retained.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    async def clear(self, run_id: str) -> None:
        path = self._path_for(run_id)
        if path.is_file():
            path.unlink()
