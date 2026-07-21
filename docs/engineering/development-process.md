# Development process

## Branching

- Default branch: `main`
- Feature branches: `phase-<n>/<short-description>`
- Hotfixes: `fix/<short-description>` (still note affected phase if known)

Keep branches short-lived. Prefer a small PR train over one large phase dump when a phase is large.

## Local loop

1. Activate `.venv`
2. Implement within phase scope
3. Run `pytest`
4. Run `ruff check .` and `ruff format .`
5. Run `mypy src`
6. Update docs / roadmap checkboxes if exit criteria moved

Optional:

```bash
pre-commit install
pre-commit run --all-files
```

## Issue discipline

- Tag issues with `phase-N`
- Bugs reference the failing phase or module
- Spikes / design notes can live as issues or under `docs/engineering/`

## Pull requests

PRs should answer:

1. Which phase does this advance?
2. What is explicitly out of scope?
3. How was it tested?
4. What docs changed?

Template sketch:

```markdown
## Phase
Phase N — <name>

## Summary
-

## Out of scope
-

## Test plan
- [ ] pytest
- [ ] ruff
- [ ] mypy
```

## API changes

- New public symbols need docstrings and `__all__` consideration
- Breaking changes require a roadmap note and migration note in docs
- Prefer protocols and adapters over hard vendor coupling

## Working with coding agents

Use `.ai/` as the instruction pack:

- [`.ai/README.md`](../../.ai/README.md)
- [`.ai/CONVENTIONS.md`](../../.ai/CONVENTIONS.md)
- [`.ai/PHASES.md`](../../.ai/PHASES.md)

Coding agents must not skip ahead to implement the agent loop before Phase 6 unless a maintainer issue overrides the roadmap.

## Definition of done (per phase)

A phase is done when:

1. Exit criteria in `ROADMAP.md` are checked
2. Tests cover the new behavior
3. Docs describe how to use or extend it
4. No temporary scaffolding is left unexplained
5. Lint and type checks pass
