# Orchestrator (Phase 6)

Phase 6 introduces the first **real agent loop**: an explicit run state machine
driven by an action selector (actor), with read-only repository tools.

## What it does

Given a `TaskSpec` (typically `mode=explain`):

1. `received → analyzing → planning → investigating`
2. Actor selects `AgentAction`s (`invoke_tool`, `revise_plan`, `finish`, …)
3. Tools run through the Phase 4 executor + Phase 2 policy jail
4. Observations/reflections land in Phase 5 working memory
5. `finish` → `reporting → completed` and an `EngineeringReport`

## Quick start

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

Stub-provider actor (JSON actions):

```python
from forgemind.agent import ProviderActionSelector
from forgemind.providers import StubProvider

provider = StubProvider(responses=['{"type":"finish","summary":"done","success":true}'])
actor = ProviderActionSelector(provider)
```

## Components

| Module | Role |
|--------|------|
| `transitions` | Legal `RunStatus` edges + `transition()` |
| `actor` | `ScriptedActionSelector`, `ProviderActionSelector` |
| `orchestrator` | Main loop, budgets, tool dispatch |
| `reporting` | `EngineeringReport` assembly |

## Read-only rules (Phase 6)

- Only `repo.*` tools are executed
- `run_tests` is rejected (logged as a system observation)
- Non-repo tools are blocked
- Write/edit capabilities wait for Phase 8

## Resume

`RunState` is serializable. Passing a terminal state back into `run(..., state=)`
returns immediately with a rebuilt report. Passing a non-terminal state continues
the loop (approval waits return `AWAITING_APPROVAL` without completing).

## Out of scope

- Full planner/reflector roles (Phase 7) — now landed; see `docs/planning/`
- Mutating edits + test loop (Phase 8)
- Dedicated reviewer component (Phase 9)
- Trace export / replay (Phase 10)
- Product CLI (Phase 11)
