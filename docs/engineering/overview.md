# Engineering overview

This document describes **how ForgeMind will be developed** as a repository — process, structure, and quality bars — before the agent itself exists.

## Mission

ForgeMind is a flagship open-source **Autonomous Software Engineering Agent**: it plans, inspects repositories, uses tools under policy, edits and tests, reflects, self-reviews, and reports — like an engineer, not a chatbot.

The differentiator is the **agent runtime** (state machine, tool orchestration, memory, reflection, approvals), not a prompt wrapper or third-party workflow framework.

## Development model

ForgeMind uses **phased, independent delivery**:

1. Work is organized into **15 phases** (see [`ROADMAP.md`](../../ROADMAP.md)).
2. Each phase ships a coherent slice: contracts, implementation, tests, and docs.
3. Phases may depend on earlier phases, but must not require unfinished later ones.
4. The minimal agent loop appears in **Phase 6**. Everything before that is infrastructure and contracts.

This bootstrap (Phase 0) establishes layout and process only.

## Source of truth

| Concern | Location |
|---------|----------|
| Phase plan and exit criteria | `ROADMAP.md` |
| Contribution rules | `CONTRIBUTING.md` |
| Engineering process | `docs/engineering/` |
| Conventions for humans and coding agents | `.ai/` |
| Library code | `src/forgemind/` |
| Tests | `tests/` |
| Tooling config | `pyproject.toml` |

## Package architecture (target)

Modules are reserved now; behavior arrives with phases:

```text
forgemind/
  core/            # types, errors, protocols
  config/          # settings and validation
  providers/       # model adapters
  tools/           # registry and invocation
  memory/          # short/long-term memory
  agent/           # runtime loop and control
  observability/   # logs, traces, run records
  cli/             # command-line interface
  api/             # optional HTTP surface
  plugins/         # extension loading
  eval/            # evaluation harness
```

Boundaries:

- **Providers** talk to models; they do not own the agent loop.
- **Tools** execute side effects; they do not choose the next step.
- **Memory** stores and retrieves; it does not call providers.
- **Agent** orchestrates; it depends on protocols, not concrete vendors.
- **Observability** observes; it does not change control flow except via explicit hooks.

## Quality bar

Every merged change should meet:

- **Scoped** to a phase or a clearly labeled cross-cutting fix
- **Typed** under `mypy --strict` for `src/`
- **Lint-clean** under Ruff
- **Tested** for new behavior (no network in unit tests)
- **Documented** when user-facing or architectural

## Release philosophy

Until Phase 14:

- Version remains pre-release (`0.x`)
- Public APIs may change with roadmap notes
- Prefer deprecations once something is documented as stable

## Related docs

- [Development process](development-process.md)
- [Architecture principles](architecture-principles.md)
- [Phase workflow](phase-workflow.md)
- [Testing strategy](testing-strategy.md)
- [Tooling](tooling.md)
