# Reviewer + engineering report (Phase 9)

ForgeMind keeps a **separate reviewer role** (ADR 0004). The actor produces
changes; the reviewer critiques them and can send the run back to acting or
testing before completion.

## Components

| Piece | Role |
|-------|------|
| `HeuristicReviewer` | Rule-based findings from working memory + diff summary |
| `ProviderReviewer` | Model JSON `ReviewReport` with heuristic fallback |
| `build_engineering_report` | Final artifact including changes, tests, and review |
| `require_review_before_completion` | Standard/strict profiles gate successful finish |

## Quick start

```python
import asyncio
from pathlib import Path

from forgemind.agent import (
    ScriptedActionSelector,
    create_mutable_orchestrator,
    fix_task,
)
from forgemind.config import profile_config
from forgemind.review import HeuristicReviewer

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
        {"type": "request_review"},
        {"type": "finish", "summary": "Fixed add()", "success": True},
    ]
)
orch = create_mutable_orchestrator(
    workspace_root=workspace,
    config=profile_config("standard"),
    actor=actor,
    reviewer=HeuristicReviewer(),
)
result = asyncio.run(orch.run(fix_task(workspace, "Fix calc tests")))
print(result.state.status, result.report.review.approve_completion if result.report else None)
```

## Behaviour

1. `request_review` enters `reviewing`, builds a diff summary from write/edit
   observations + test summaries, and stores `WorkingMemory.last_review`.
2. Blocking findings (`approve_completion=false` or high/critical) resume in
   `acting` or `testing`.
3. On mutable runs with `require_review_before_completion=true`, a successful
   `finish` auto-runs review when none exists yet.
4. Approved reviews proceed to `reporting` / `completed`; the engineering
   report embeds the `ReviewReport`, inferred `changes`, and `tests_run`.

## Config

| Setting | Readonly | Standard | Strict |
|---------|----------|----------|--------|
| `require_review_before_completion` | false | true | true |

Env: `FORGEMIND_REQUIRE_REVIEW_BEFORE_COMPLETION=true|false`

## Golden reports

Use `report_dict_for_golden(report)` to drop timestamps for stable comparisons.
