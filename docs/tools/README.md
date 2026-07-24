# Tools

ForgeMind side effects go through **registered tools**. The runtime owns the
registry, argument validation, and policy-aware executor. The model never gets
raw filesystem or shell access.

---

## Built-in tools

| Name | Purpose | Permission | Risk |
|------|---------|------------|------|
| `repo.list_structure` | List files/dirs under a workspace path | `repo.read` | READ |
| `repo.search` | Substring search across text files | `repo.read` | READ |
| `repo.read_file` | Read a text file (with line windowing) | `repo.read` | READ |
| `repo.write_file` | Create or overwrite a text file | `repo.write` | WRITE |
| `repo.edit_file` | Exact string replacement in a text file | `repo.write` | WRITE |
| `test.run` | Run pytest in the workspace (optional selector) | `test.run` | EXEC |

Read tools ship with `create_readonly_tooling`. Write + test tools are included
in `create_standard_tooling` (Phase 8).

---

## Quick start

```python
import asyncio
from pathlib import Path

from forgemind.config import profile_config
from forgemind.tools import create_readonly_tooling, create_standard_tooling

workspace = Path(".")

# Survey only
readonly = create_readonly_tooling(
    workspace_root=workspace,
    config=profile_config("readonly"),
)
print(asyncio.run(readonly.invoke("repo.search", {"query": "TODO"})).status)

# Edit + test
mutable = create_standard_tooling(
    workspace_root=workspace,
    config=profile_config("standard"),
)
asyncio.run(
    mutable.invoke(
        "repo.edit_file",
        {"path": "src/app.py", "old_string": "old", "new_string": "new"},
    )
)
print(asyncio.run(mutable.invoke("test.run", {"selector": "tests/"})).output["passed"])
```

---

## Architecture

```text
ToolCall
   │
   ▼
ToolExecutor ──► PolicyEngine (permissions + path jail/denylist)
   │
   ▼
InMemoryToolRegistry.get(name)
   │
   ▼
BaseTool.execute ──► validate args ──► run()
   │
   ▼
ToolResult ──► Observation (optional)
```

- **Registry** owns tool instances by name.
- **Executor** authorizes first; denied calls return `ToolResultStatus.DENIED`.
- **Tools** never get a raw host handle from the LLM — only validated arguments.

---

## Argument validation

Manifests declare a JSON-schema-like `ToolParameterSchema`:

- required keys
- property types (`string`, `integer`, `number`, `boolean`, `object`, `array`)
- `additional_properties=false` by default

Invalid arguments become `ToolResultStatus.ERROR`.

---

## Safety

1. Paths resolve under `workspace_root` (`PermissionDeniedError` / DENIED on escape).
2. Policy denylist blocks `.env`, secrets globs, etc. (writes included).
3. Search skips heavy dirs (`.git`, `node_modules`, `.venv`, …).
4. Read/search/write cap file size; `test.run` has a process timeout.
5. Mutable orchestrator terminates the run on write denylist hits.

Git mutation tools arrive in later phases.

---

## Extending

```python
from forgemind.tools import BaseTool, InMemoryToolRegistry

class MyTool(BaseTool):
    @property
    def manifest(self): ...
    async def run(self, arguments): ...

registry = InMemoryToolRegistry()
registry.register(MyTool(...))
```

Keep side effects inside `run()`. Prefer returning JSON-serializable dicts.
