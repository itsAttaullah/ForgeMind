# ADR 0003: Explicit run state machine

- **Status:** Accepted
- **Date:** 2026-07-20
- **Deciders:** ForgeMind maintainers

## Context

Chat-transcript-centric agents hide control flow inside message history, making resume, permissions, and debugging difficult.

## Decision

Every ForgeMind execution is an `AgentRun` driven by an **explicit state machine** (e.g. Analyzing → Planning → Investigating → Acting → Reflecting → Testing → Reviewing → Reporting → Completed).

- Transitions are guarded by policy, budgets, and schema validation
- `RunState` is serializable for resume and audit
- Message history is an input to decision roles, not the source of control truth

## Consequences

### Positive

- Clear lifecycle for UI/CLI and approvals
- Deterministic tests for illegal transitions
- Natural place for human gates

### Negative / trade-offs

- Up-front design cost
- Risk of over-rigid states if not kept coarse enough

## Alternatives considered

- Pure ReAct loop with no named phases (harder approvals/reporting)
- Heavyweight workflow engines (overkill for v1)
