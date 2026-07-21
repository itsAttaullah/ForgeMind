# Core contracts (Phase 1)

This document freezes ForgeMind’s public **domain types** and **ports** introduced in Phase 1.

Implementation of orchestrator, tools, and providers comes in later phases. Phase 1 only defines **serializable contracts** and **structural protocols**.

Architecture context: [`../architecture/PROPOSAL.md`](../architecture/PROPOSAL.md)

---

## Design rules

1. **LLM decides; runtime validates** — model outputs must parse as `AgentAction` or they are rejected (`InvalidActionError`).
2. **`extra="forbid"`** on domain models — unknown fields (including accidental CoT keys) are rejected.
3. **Summary-only reflection** — `ReflectionSummary` stores public learnings, never private chain-of-thought.
4. **Protocols over implementations** — `ModelProvider`, `Tool`, `MemoryStore`, `Planner`, `Reflector`, `Reviewer`, `ActionSelector`, `ToolRegistry`.

---

## Domain types

| Type | Module | Purpose |
|------|--------|---------|
| `TaskSpec` | `forgemind.core.task` | User goal, workspace, mode, permissions |
| `RunState` | `forgemind.core.state` | Serializable run control state + budgets |
| `ExecutionPlan` / `PlanStep` | `forgemind.core.plan` | Structured plan |
| `AgentAction` | `forgemind.core.actions` | Discriminated next-move union |
| `ToolCall` / `ToolResult` / `ToolManifest` | `forgemind.core.tools` | Tool envelopes |
| `Observation` | `forgemind.core.tools` | Model-facing tool/system observation |
| `WorkingMemory` / `MemorySnapshot` | `forgemind.core.memory` | Memory slices |
| `ReflectionSummary` | `forgemind.core.reflection` | Post-action evaluation |
| `ReviewReport` / `ReviewFinding` | `forgemind.core.review` | Self-review output |
| `ApprovalRequest` / `ApprovalResponse` | `forgemind.core.approval` | Human gates |
| `EngineeringReport` | `forgemind.core.report` | Final deliverable |
| `TraceEvent` | `forgemind.core.report` | Observability event |
| `ChatMessage` / `ProviderRequest` / `ProviderResponse` | `forgemind.core.messages` / `provider` | LLM I/O |
| Enums | `forgemind.core.enums` | `RunStatus`, `Permission`, `RiskClass`, … |
| Errors | `forgemind.core.errors` | `ForgeMindError` hierarchy |

Import from the package root for the stable surface:

```python
from forgemind import TaskSpec, RunState, parse_agent_action
from forgemind.core import ExecutionPlan, InvokeToolAction, RunStatus
```

---

## `AgentAction` discriminator

| `type` | Meaning |
|--------|---------|
| `invoke_tool` | Execute a registered tool |
| `revise_plan` | Replace the current plan |
| `request_approval` | Pause for human/policy approval |
| `run_tests` | Enter/continue the test loop |
| `request_review` | Trigger the reviewer role |
| `finish` | Actor believes the task is done |
| `abort` | Stop with a public reason |

Parse untrusted payloads with:

```python
from forgemind import parse_agent_action, InvalidActionError

try:
    action = parse_agent_action(payload)
except InvalidActionError:
    ...
```

Invalid examples that **must** raise `InvalidActionError`:

- missing `type`
- unknown `type`
- empty required strings (`tool_name`, `summary`, `reason`)
- empty `plan.steps`
- extra forbidden fields

---

## `RunStatus` lifecycle

`received → analyzing → planning → investigating → acting → reflecting → testing → reviewing → awaiting_approval → reporting → completed | failed | aborted`

Terminal: `completed`, `failed`, `aborted` (`RunState.is_terminal`).

Transition enforcement is **Phase 6** (orchestrator). Phase 1 only defines the enum and state container.

---

## Protocols (ports)

| Protocol | Responsibility |
|----------|----------------|
| `ModelProvider` | `complete(ProviderRequest) -> ProviderResponse` |
| `Tool` | `manifest` + `execute(ToolCall) -> ToolResult` |
| `ToolRegistry` | Lookup manifests / tools |
| `MemoryStore` | Working + long-term memory |
| `Planner` | Create / revise `ExecutionPlan` |
| `Reflector` | Produce `ReflectionSummary` |
| `Reviewer` | Produce `ReviewReport` |
| `ActionSelector` | Choose next `AgentAction` |

All are `typing.Protocol` (runtime-checkable where useful). No concrete adapters in Phase 1.

---

## Serialization

All Pydantic models support:

```python
data = model.model_dump(mode="json")
restored = Model.model_validate(data)
```

`Path` fields on `TaskSpec` coerce from strings. Timestamps use timezone-aware UTC.

---

## Out of scope (later phases)

- Config/policy engine (Phase 2)
- Real providers (Phase 3)
- Tool executor (Phase 4)
- Memory backends (Phase 5)
- Orchestrator / transitions (Phase 6+)
