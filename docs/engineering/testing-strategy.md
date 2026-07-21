# Testing strategy

## Goals

- Catch regressions early without requiring live model APIs
- Keep unit tests fast and deterministic
- Introduce integration and eval layers as phases need them

## Layers

| Layer | Location | When |
|-------|----------|------|
| Smoke | `tests/unit/test_smoke.py` | Phase 0+ |
| Unit | `tests/unit/` | Every phase that adds logic |
| Integration | `tests/integration/` | Providers, loop, API |
| Eval | `src/forgemind/eval` + scenarios | Phase 12 |
| Example import checks | CI / scripts | Phase 13 |

## Rules

1. **No network in unit tests** — use fakes, stubs, and recorded fixtures.
2. **Inject dependencies** — providers, clocks, and I/O are constructor or parameter seams.
3. **Assert behavior, not logs alone** — prefer structured results and return values.
4. **One failure mode per test** — keep tests readable.
5. **Markers** — use `@pytest.mark.unit`, `integration`, or `slow` as suites grow.

## Commands

```bash
pytest
pytest tests/unit -m unit
pytest --cov=forgemind --cov-report=term-missing
```

Coverage floor starts at `0` during bootstrap and will rise as phases land. Phase exit criteria may set higher bars for specific packages.

## Fixtures

Shared fixtures live in `tests/conftest.py`. Phase-specific fixtures should live near the tests that need them (e.g. `tests/unit/tools/conftest.py`) once those trees exist.

## What “good” looks like per phase

- New public function/class → unit tests for happy path and key failures
- New protocol → fake implementation used by agent/unit tests
- New CLI/API → smoke tests for help/health plus one success path
- New guardrail → tests that prove the stop reason

## Out of scope for Phase 0

- Load / performance suites
- Live provider contract tests
- Mutation testing

Those may be proposed later without blocking the roadmap.
