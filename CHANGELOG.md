# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/) once
releases begin (see Roadmap Phase 14).

## [Unreleased]

### Added

- Phase 8 write/edit tools: `repo.write_file`, `repo.edit_file`
- `test.run` pytest runner tool and `create_standard_tooling`
- Mutable orchestrator (`create_mutable_orchestrator`) with repair-budget loop
- Repair fixture (`tests/fixtures/repair_repo/`) and fix-loop E2E tests
- `fix_task` helper and ACTING↔TESTING transitions for the repair path

- Phase 7 planner/reflector: heuristic + provider implementations
- Orchestrator integration for plan creation and reflection-driven plan revision
- Summary-only reflection sanitization before memory writes
- Planning docs (`docs/planning/README.md`)

- Phase 6 orchestrator: explicit run state machine and read-only agent loop
- Scripted and provider-backed action selectors
- Engineering report assembly for completed/failed runs
- Orchestrator docs (`docs/agent/README.md`)

- Phase 5 memory system: working + long-term stores, retention budgets, snapshots
- In-memory and JSON file backends (`create_memory_store`)
- CoT/metadata sanitization for summary-only persistence
- Memory documentation (`docs/memory/README.md`)

- Phase 4 tool runtime: registry, argument validation, policy-aware executor
- Read-only repo tools: `repo.list_structure`, `repo.search`, `repo.read_file`
- Sample fixture repository under `tests/fixtures/sample_repo/`
- Tools documentation (`docs/tools/README.md`)

- Phase 3 model providers: `StubProvider` and `OpenAICompatibleProvider`
- Provider factory (`create_provider`) wired to config `provider.kind`
- Normalized `ProviderResponse` mapping and `ProviderError` HTTP details
- Provider documentation (`docs/providers/README.md`)

- Phase 2 config system: layered loader (defaults → file → env → overrides)
- Built-in profiles `readonly`, `standard`, `strict` with example TOML under `configs/`
- Policy engine with permission checks, workspace path jail, allow/deny globs, approval triggers
- Budget assertion helpers (steps, tool calls, repairs, optional USD cost)
- Profile documentation (`docs/config/profiles.md`)

- Phase 1 core domain types, enums, errors, and protocols (`forgemind.core`)
- `parse_agent_action` validation with `InvalidActionError` for malformed LLM payloads
- Contracts documentation (`docs/contracts/README.md`)
- Pydantic v2 runtime dependency

### Changed

- Package version bumped to `0.1.0.dev0`
- Orchestrator factories seed budget counters from profile config

## [0.0.0] — 2026-07-20

### Added

- Architecture proposal for Autonomous Software Engineering Agent (`docs/architecture/PROPOSAL.md`)
- Initial ADRs 0001–0006 (`docs/adr/`)
- Roadmap realigned to ASE phases (0–14)
- Repository bootstrap (Phase 0): package layout, docs, tooling, and smoke tests
- Engineering documentation under `docs/engineering/`
- Agent guidance under `.ai/`
