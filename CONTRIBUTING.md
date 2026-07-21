# Contributing to ForgeMind

Thanks for helping build ForgeMind. This project is developed in **independent phases** (see [`ROADMAP.md`](ROADMAP.md)). Contributions should map to a phase whenever possible.

## Ground rules

- Do not implement unfinished roadmap phases “early” unless an issue explicitly asks for it.
- Prefer small, reviewable pull requests.
- Every behavior change needs tests.
- Every user-facing change needs docs.
- Do not commit secrets, API keys, or personal environment files.
- Do not commit or push from automation unless a maintainer explicitly requests it.

## Development setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

Optional: install pre-commit hooks if you use them locally:

```bash
pre-commit install
```

## Workflow

1. **Pick a phase** — open or claim an issue tagged with a phase number.
2. **Branch** — `phase-<n>/<short-description>` (example: `phase-1/core-types`).
3. **Implement** — stay inside the phase scope; leave TODOs for later phases.
4. **Test** — `pytest`
5. **Lint** — `ruff check .` and `ruff format .`
6. **Types** — `mypy src`
7. **Document** — update `docs/` and roadmap checkboxes when exit criteria are met.
8. **Open a PR** — link the phase and include a short test plan.

## Code standards

- Python 3.11+
- Src layout only: library code lives in `src/forgemind/`
- Public APIs are explicit; avoid leaking internal modules
- Prefer typed interfaces and clear error types
- No network calls in unit tests; use fakes/stubs
- Keep modules focused; avoid god-objects in the agent core

See also:

- [`docs/engineering/architecture-principles.md`](docs/engineering/architecture-principles.md)
- [`docs/engineering/development-process.md`](docs/engineering/development-process.md)
- [`.ai/CONVENTIONS.md`](.ai/CONVENTIONS.md)

## Testing

```bash
pytest
pytest --cov=forgemind --cov-report=term-missing
```

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/` (added as phases need them)
- Eval scenarios: introduced in Phase 12

## Linting and formatting

```bash
ruff check .
ruff format .
mypy src
```

Configuration lives in `pyproject.toml`.

## Documentation

- Engineering process: `docs/engineering/`
- Phase plan: `ROADMAP.md`
- Agent/tooling guidance: `.ai/`

When you change behavior, update the docs in the same PR.

## Pull request checklist

- [ ] Scoped to one roadmap phase (or a clearly labeled cross-cutting fix)
- [ ] Tests added or updated
- [ ] Lint and type checks pass
- [ ] Docs updated
- [ ] No secrets committed
- [ ] ROADMAP exit criteria updated if the phase is complete

## Issues

- Bug reports: include reproduction steps, expected vs actual, and environment.
- Feature requests: tie them to a roadmap phase or propose a new phase with rationale.
- Security reports: do not file publicly if sensitive; contact maintainers privately.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
