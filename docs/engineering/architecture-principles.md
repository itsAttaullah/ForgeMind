# Architecture principles

These principles guide ForgeMind as phases land. They are constraints, not slogans.

## 1. Explicit state

Agent runs expose structured state: messages, tool calls, stop reasons, and errors. Hidden global mutable context is avoided.

## 2. Protocols over vendors

Model providers, tools, memory backends, and planners are interfaces. Reference implementations exist, but the core depends on protocols.

## 3. Side effects live in tools

The agent loop decides; tools execute. Network, filesystem, and process side effects belong behind tool boundaries with validation.

## 4. Failure is a first-class outcome

Tool failures, provider failures, and guardrail stops produce typed results — not silent retries without policy.

## 5. Inspectability by default

Every run should be reconstructable from logs/traces enough to debug “why did it do that?” Observability is not an optional plugin bolted on at the end.

## 6. Test seams everywhere

Providers and clocks are injectable. Unit tests never require live network or paid APIs.

## 7. Small public surface

Prefer a narrow, stable export surface. Internal modules may move; public APIs change deliberately.

## 8. Phase-shaped modules

Package folders map to roadmap capabilities. Do not collapse unrelated concerns into a single “utils” mega-module.

## 9. Security-aware extensions

Plugins and tools are untrusted capability surfaces. Loading and invocation must be explicit and reviewable (Phase 11 / 14).

## 10. Progressive disclosure

Simple agents stay simple. Planning, evals, HTTP API, and plugins remain optional layers.

## Non-goals (near term)

- Being a full ML training framework
- Shipping a hosted multi-tenant SaaS in this repository
- Hiding the agent loop behind opaque “magic” APIs
- Supporting every provider on day one

## Evolution

Principles can change, but changes need a short ADR-style note under `docs/engineering/` and a roadmap mention if they affect phase scope.
