# ForgeMind conventions

## Language and runtime

- Python 3.11+
- Prefer stdlib first; add dependencies only when a phase needs them
- Use `from __future__ import annotations` in new modules

## Layout

- Library code: `src/forgemind/`
- Tests: `tests/unit/`, `tests/integration/`
- Docs: `docs/`
- Do not place package code at the repo root

## Style

- Formatter/linter: Ruff (see `pyproject.toml`)
- Types: strict mypy on `src/`
- Docstrings for public modules, classes, and functions
- Errors: prefer specific exception types over bare `Exception`

## Naming

- Packages/modules: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Protocols / interfaces: descriptive nouns (`ModelProvider`, `Tool`, `MemoryStore`)

## Public API

- Export deliberately via `__all__`
- Prefer stable names early; rename is cheap only before Phase 14 freeze
- Avoid importing private `_modules` from outside their package

## Testing

- Name tests `test_<behavior>`
- No live network in unit tests
- Put shared fixtures in `conftest.py`

## Docs

- Update roadmap checkboxes when exit criteria move
- Keep examples truthful (no fake APIs that do not exist yet)
- Prefer short engineering notes over long speculative design essays

## Git

- Commit only when the user asks
- Never push unless explicitly requested
- Never commit secrets or `.env`
