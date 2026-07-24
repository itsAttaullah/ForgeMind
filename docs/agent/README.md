# Orchestrator

The orchestrator drives an explicit run state machine. Actors select
`AgentAction`s; tools, memory, planner, and reflector are runtime-owned.

## Modes

| Factory | Tools | Typical task |
|---------|-------|--------------|
| `create_readonly_orchestrator` | list / search / read | `explain_task` |
| `create_mutable_orchestrator` | + write / edit / `test.run` | `fix_task` |

## Quick start (read-only)

```python
import asyncio
from pathlib import Path

from forgemind.agent import (
    ScriptedActionSelector,
    create_readonly_orchestrator,
    explain_task,
)
from forgemind.config import profile_config

workspace = Path("tests/fixtures/sample_repo")
actor = ScriptedActionSelector(
    [
        {"type": "invoke_tool", "tool_name": "repo.list_structure", "arguments": {"path": "."}},
        {"type": "finish", "summary": "Survey complete", "success": True},
    ]
)
orch = create_readonly_orchestrator(
    workspace_root=workspace,
    config=profile_config("readonly"),
    actor=actor,
)
result = asyncio.run(orch.run(explain_task(workspace, "Explain this repository")))
print(result.state.status, result.report.key_findings if result.report else None)
```

## Quick start (fix / repair loop)

```python
import asyncio
from pathlib import Path

from forgemind.agent import (
    ScriptedActionSelector,
    create_mutable_orchestrator,
    fix_task,
)
from forgemind.config import profile_config

workspace = Path("tests/fixtures/repair_repo")
actor = ScriptedActionSelector(
    [
        {
            "type": "invoke_tool",
            "tool_name": "repo.edit_file",
            "arguments": {
                "path": "calc.py",
                "old_string": "return left + right + 1",
                "new_string": "return left + right",
            },
        },
        {"type": "run_tests", "selector": "test_calc.py"},
        {"type": "finish", "summary": "Fixed add()", "success": True},
    ]
)
orch = create_mutable_orchestrator(
    workspace_root=workspace,
    config=profile_config("standard"),
    actor=actor,
)
result = asyncio.run(orch.run(fix_task(workspace, "Make calc tests pass")))
print(result.state.status)
```

## Loop behaviour (Phase 8+)

1. Write/edit tools move the run into `acting`, then `reflecting`.
2. `run_tests` / `test.run` move into `testing`; failures consume **repair iterations**.
3. After a failed test (within budget), the run resumes in `acting` for another fix.
4. Hard **denylist** writes (e.g. `.env`) fail the run immediately.
5. Exceeding `max_repair_iterations` fails the run with a budget error.
6. Profile budgets are seeded via `create_*_orchestrator` (`seed_budgets_from_config`).
7. On mutable standard/strict profiles, successful `finish` requires a reviewer pass
   (see `docs/review/README.md`).

## Components

| Module | Role |
|--------|------|
| `transitions` | Legal `RunStatus` edges + `transition()` |
| `actor` | `ScriptedActionSelector`, `ProviderActionSelector` |
| `orchestrator` | Main loop, budgets, tool dispatch |
| `reporting` | `EngineeringReport` assembly |

## Resume

`RunState` is serializable. Passing a terminal state back into `run(..., state=)`
returns immediately with a rebuilt report. Passing a non-terminal state continues
the loop (approval waits return `AWAITING_APPROVAL` without completing).

## Out of scope

- Trace export / replay (Phase 10)
- Product CLI (Phase 11)
- Git mutation / approval UX (Phase 12)
