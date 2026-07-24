# Planner + reflection (Phase 7)

Phase 7 adds first-class **Planner** and **Reflector** roles used by the
orchestrator. Only public summaries are stored — private chain-of-thought is
stripped before memory writes.

## Components

| Component | Module | Role |
|-----------|--------|------|
| `HeuristicPlanner` | `forgemind.planning` | Deterministic mode-aware `ExecutionPlan` |
| `ProviderPlanner` | `forgemind.planning` | JSON plan from a model provider (+ heuristic fallback) |
| `HeuristicReflector` | `forgemind.reflection` | Rule-based `ReflectionSummary` |
| `ProviderReflector` | `forgemind.reflection` | JSON reflection from a model (+ sanitize/fallback) |

## Orchestrator wiring

On run start (PLANNING):

1. `planner.create_plan(state, snapshot)`
2. Persist plan on `RunState` + working memory

After each significant tool observation:

1. Transition to `reflecting`
2. `reflector.reflect(...)` → sanitized `ReflectionSummary`
3. If `verdict == revise_plan`, call `planner.revise_plan(...)` and store the new plan
4. Return to `investigating`

## Summary-only invariant

Reflections pass through `sanitize_reflection()`:

- Truncates `learned` / hints to budget limits
- Drops metadata keys like `chain_of_thought`, `cot`, `scratchpad`

## Quick example

```python
from forgemind.planning import HeuristicPlanner
from forgemind.reflection import HeuristicReflector
from forgemind.agent import create_readonly_orchestrator, ScriptedActionSelector

orch = create_readonly_orchestrator(
    workspace_root=".",
    config=profile_config("readonly"),
    actor=ScriptedActionSelector([...]),
    planner=HeuristicPlanner(),
    reflector=HeuristicReflector(),
)
```

## Out of scope

- Write / edit / test repair loop (Phase 8) — landed; see `docs/tools/` and `docs/agent/`
- Dedicated reviewer role (Phase 9)
