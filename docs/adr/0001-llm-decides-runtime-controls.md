# ADR 0001: LLM decides; runtime controls

- **Status:** Accepted
- **Date:** 2026-07-20
- **Deciders:** ForgeMind maintainers

## Context

ForgeMind is an Autonomous Software Engineering agent. A common failure mode in agent products is either (a) giving the model too much host power, or (b) reducing the model to a scripted workflow with no real decision-making.

We need a clear authority split.

## Decision

- The **LLM** chooses: next action, which tool, whether to investigate further, whether the task is complete, and how to revise the plan.
- The **application runtime** owns: available tools, permissions, execution, state, memory persistence, budgets, approvals, and safety boundaries.
- The LLM must never directly access the filesystem or execute commands.

## Consequences

### Positive

- Real agency inside hard safety boundaries
- Testable control plane independent of model quality
- Clear mental model for contributors

### Negative / trade-offs

- More orchestration code than a “prompt + tools” demo
- Requires robust action schemas and validation

## Alternatives considered

- Fully scripted DAG workflows (insufficient autonomy)
- Unrestricted shell agent (unacceptable risk)
- Third-party agent frameworks owning the loop (see ADR 0006)
