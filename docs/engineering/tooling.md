# Tooling

## Package and build

- Build backend: Hatchling
- Layout: `src/forgemind`
- Config: `pyproject.toml`

```bash
pip install -e ".[dev]"
```

## Lint and format

Ruff handles linting and formatting:

```bash
ruff check .
ruff check . --fix
ruff format .
```

Settings live under `[tool.ruff]` in `pyproject.toml`.

## Types

```bash
mypy src
```

`mypy` runs in strict mode for `src/`. Tests may be looser via overrides.

## Tests

```bash
pytest
pytest --cov=forgemind --cov-report=term-missing
```

## Pre-commit

Optional local hooks:

```bash
pip install -e ".[dev]"
pre-commit install
pre-commit run --all-files
```

Config: `.pre-commit-config.yaml`

## Environment

- Copy `.env.example` → `.env` for local secrets (never commit `.env`)
- Runtime artifacts should land under ignored paths (see `.gitignore`)

## CI expectations (future)

When CI is added, the minimum gate should be:

1. `ruff check .`
2. `ruff format --check .`
3. `mypy src`
4. `pytest`

Phase 0 does not require a specific CI vendor; keep commands portable.
