# `.ai/` — guidance for humans and coding agents

This folder is the instruction pack for developing ForgeMind with AI coding assistants and for human contributors who want concise engineering norms.

## Contents

| File | Purpose |
|------|---------|
| [`CONVENTIONS.md`](CONVENTIONS.md) | Code and docs conventions |
| [`PHASES.md`](PHASES.md) | Phase guardrails for agents |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Target architecture sketch |
| [`prompts/phase-bootstrap.md`](prompts/phase-bootstrap.md) | Prompt template for phase work |
| [`prompts/review.md`](prompts/review.md) | Prompt template for PR review |

## Rules for coding agents

1. Read `ROADMAP.md` and `PHASES.md` before implementing.
2. Do **not** build the agent loop before Phase 6.
3. Do **not** commit or push unless the user explicitly asks.
4. Prefer editing within the active phase scope.
5. Keep changes small, tested, and documented.
6. Match existing style; do not invent parallel frameworks.

## Relationship to `docs/`

- `docs/engineering/` is the long-form source of truth for process.
- `.ai/` is the short, agent-oriented checklist layer.
- If they diverge, fix both in the same change.
