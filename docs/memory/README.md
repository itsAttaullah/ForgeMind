# Memory system (Phase 5)

ForgeMind memory is split into:

| Layer | Scope | Purpose |
|-------|-------|---------|
| **Working memory** | One `run_id` | Task, plan, observations, reflections, files inspected |
| **Long-term memory** | Workspace / project | Summarized facts and strategies reused across runs |

**Invariant:** only public summaries are stored. Private chain-of-thought keys
(`chain_of_thought`, `cot`, `scratchpad`, …) are stripped on write.

---

## Quick start

```python
import asyncio

from forgemind.core.memory import LongTermMemoryItem, WorkingMemory
from forgemind.core.tools import Observation
from forgemind.memory import create_memory_store

store = create_memory_store()  # in-memory backends

async def main() -> None:
    memory = WorkingMemory(task_brief="Add JWT auth")
    memory.observations.append(
        Observation(source="tool:repo.search", summary="Found auth package")
    )
    await store.save_working("run-1", memory)
    await store.remember(
        LongTermMemoryItem(
            key="auth-strategy",
            content="Extend existing auth with JWT middleware",
            kind="strategy",
        )
    )
    snap = await store.snapshot("run-1", query="JWT auth")
    print(snap.working.task_brief, [item.key for item in snap.long_term])

asyncio.run(main())
```

Persistent backends:

```python
store = create_memory_store(
    working_dir=".forgemind/memory/working",
    long_term_path=".forgemind/memory/long_term.json",
)
```

---

## Budgets / retention

`MemoryBudget` caps how much is retained and injected:

- max observations / reflections / files / blockers / hypotheses / tests
- max long-term items in a snapshot
- max characters for observation summaries and reflection `learned` text

`apply_retention()` keeps the **most recent** items and sanitizes summaries.

---

## APIs

### Working stores

- `InMemoryWorkingStore` — process local
- `JsonFileWorkingStore` — one JSON file per run

Helpers: `append_observation`, `append_reflection`, `set_plan`, `note_file`

### Long-term stores

- `InMemoryLongTermStore`
- `JsonFileLongTermStore`

Retrieval uses simple token-overlap scoring (`score_item`). Good enough for
Phase 5; embeddings can replace this later without changing the port.

### Composite (`MemoryStore` port)

`CompositeMemoryStore` implements:

- `load_working` / `save_working`
- `retrieve_long_term`
- `snapshot(run_id, query=...)`
- `remember(item)` (upsert summarized long-term knowledge)

---

## What not to store

- Raw model chain-of-thought / hidden scratchpads
- Secrets, API keys, `.env` contents
- Huge file bodies (prefer paths + short observations from tools)

---

## Next phases

The orchestrator (Phase 6) will load/save working memory each step and call
`snapshot()` when building provider context.
