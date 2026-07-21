# ADR 0006: Framework independence

- **Status:** Accepted
- **Date:** 2026-07-20
- **Deciders:** ForgeMind maintainers

## Context

Agent frameworks accelerate demos but often obscure the runtime, couple products to vendor abstractions, and make ASE-specific state machines awkward.

ForgeMind’s differentiator is the **runtime design**, not prompt chaining convenience.

## Decision

- The **core orchestrator is first-party code**
- No LangChain / LlamaIndex / CrewAI / etc. as a required core dependency
- Provider SDKs or thin HTTP clients may be used behind the provider port
- Optional integrations must remain adapters, never the control plane

## Consequences

### Positive

- Full control over lifecycle, policy, and memory
- Clear teaching/portfolio artifact of “how agents really work”
- Easier long-term maintenance of ASE-specific features

### Negative / trade-offs

- More code to write early
- Fewer batteries-included connectors initially

## Alternatives considered

- Build on LangChain AgentExecutor / LangGraph (rejected for core)
- Fork an existing coding agent (rejected; goal is to design the runtime)
