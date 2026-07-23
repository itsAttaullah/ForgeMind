# Phase guardrails for coding agents

ForgeMind is an **Autonomous Software Engineering Agent** built in **15 phases** (0–14).

Canonical docs:

- [`docs/architecture/PROPOSAL.md`](../docs/architecture/PROPOSAL.md)
- [`ROADMAP.md`](../ROADMAP.md)
- [`docs/adr/`](../docs/adr/)

## Current state

- **Active:** Phase 7 (planner + reflection)
- **Mutating edits / test loop:** Phase 8+
- **Version:** `0.1.0.dev0`

## Hard stops

| Do not… | Until |
|---------|-------|
| Implement write/edit tools or test-repair loop | Phase 8 |
| Wire dedicated reviewer component | Phase 9 |
| Wire product CLI entrypoint | Phase 11 |
| Add git mutation / approval UX | Phase 12 |
| Add GitHub mutation tools | Phase 13 |
| Add plugin loader / release hardening | Phase 14 |
| Depend on LangChain/etc. in core | Ever (ADR 0006) |
| Give the model raw FS/shell access | Ever (ADR 0001/0002) |
| Persist private chain-of-thought | Ever |

Phase 7 may implement planner/reflector only (no write tools).

## Before writing code

1. Identify target phase from `ROADMAP.md`
2. Read proposal + relevant ADRs
3. Stay inside phase scope
4. Add tests and docs in the same effort

## If asked to skip ahead

Explain the phase boundary; offer contracts/stubs only; do not silently implement later phases.
