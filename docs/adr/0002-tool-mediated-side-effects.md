# ADR 0002: Tool-mediated side effects only

- **Status:** Accepted
- **Date:** 2026-07-20
- **Deciders:** ForgeMind maintainers

## Context

Software engineering agents need to read/write files, run tests, and inspect git. Direct model access to the host is unsafe and hard to audit.

## Decision

All side effects go through **registered tools**:

1. Model emits a structured tool call / action
2. Runtime validates schema
3. Policy engine authorizes permissions and paths
4. Tool executor performs the operation
5. Normalized `ToolResult` / `Observation` returns to the run

Tools are modular plugins with declarative manifests (name, schema, risk class, permissions).

## Consequences

### Positive

- Auditable traces
- Permissioning and path jails
- Easy fakes for tests

### Negative / trade-offs

- Slightly higher latency per action
- Tool surface must be designed carefully (too coarse or too fine both hurt)

## Alternatives considered

- Raw shell as the primary interface (rejected for core profiles)
- Implicit framework tool calling without an app-owned registry (rejected)
