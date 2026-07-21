# Target architecture (sketch)

Canonical design: [`docs/architecture/PROPOSAL.md`](../docs/architecture/PROPOSAL.md)  
Decisions: [`docs/adr/`](../docs/adr/)

## One-sentence model

**LLM decides next actions; ForgeMind runtime controls tools, permissions, state, memory, and safety.**

## Planes

1. **Decision plane** — Planner, Actor, Reflector, Reviewer (LLM-backed roles)
2. **Control plane** — Orchestrator, state machine, policy, approvals, memory, traces, reports
3. **Capability plane** — Tool registry/executor (repo, edit, test, git, GitHub)

## Invariants

- No direct filesystem/shell access from the model
- Explicit `RunState` machine (not chat-as-control-flow)
- Reflection stores summaries only (no private CoT)
- Separate reviewer pass before successful completion (standard profile)
- Risky git/GitHub ops require human approval

## Package map

See proposal §7–8 and reserved packages under `src/forgemind/`. New ASE modules (`planning`, `reflection`, `review`, `policy`, `approval`, `reporting`, `intelligence`) are introduced as phases land.
