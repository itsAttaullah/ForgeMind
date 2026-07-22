# Tools (Phase 4)

ForgeMind side effects go through **registered tools**. Phase 4 ships the tool
runtime (registry + executor + argument validation) and three **read-only**
repository tools.

---

## Built-in tools

| Name | Purpose | Permission |
|------|---------|------------|
| `repo.list_structure` | List files/dirs under a workspace path | `repo.read` |
| `repo.search` | Substring search across text files | `repo.read` |
| `repo.read_file` | Read a text file (with line windowing) | `repo.read` |

All three are `RiskClass.READ` and run inside the workspace jail + policy denylist.

---

## Quick start

```python
import asyncio
from pathlib import Path

from forgemind.config import profile_config
from forgemind.tools import create_readonly_tooling

workspace = Path(".")
executor = create_readonly_tooling(
    workspace_root=workspace,
    config=profile_config("readonly"),
)

result = asyncio.run(executor.invoke("repo.search", {"query": "TODO"}))
print(result.status, result.output)
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
- **Executor** authorizes first; denied calls return `ToolResultStatus.DENIED` (they do not raise).
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
2. Policy denylist blocks `.env`, secrets globs, etc. (see profiles).
3. Search skips heavy dirs (`.git`, `node_modules`, `.venv`, …).
4. Read/search cap file size / result counts.

Write / edit / test / git tools arrive in later phases.

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
