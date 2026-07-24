# ForgeMind Roadmap

ForgeMind is an **Autonomous Software Engineering Agent**, built across **15 independent phases** (0–14). Each phase ships as a coherent, reviewable increment: scoped APIs, tests, docs, and ADR updates when decisions change.

Architecture source of truth: [`docs/architecture/PROPOSAL.md`](docs/architecture/PROPOSAL.md)

**Legend**

| Status | Meaning |
|--------|---------|
| Planned | Not started |
| Active | Currently in scope |
| Done | Accepted and merged |

---

## Phase 0 — Repository foundation

**Status:** Done

**Goals**

- Package layout, tooling, contribution norms
- Architecture proposal + ADRs
- No agent behavior yet

**Exit criteria**

- [x] README, ROADMAP, CONTRIBUTING, LICENSE
- [x] `pyproject.toml`, linting, testing smoke setup
- [x] `docs/` and `.ai/` guidance
- [x] Architecture proposal + initial ADRs
- [x] Project folders with placeholder packages

---

## Phase 1 — Core types and contracts

**Status:** Done  
**Branch:** `feat/core-types`

**Goals**

- Domain types: `TaskSpec`, `RunState`, `ExecutionPlan`, `AgentAction`, `ToolResult`, reports
- Protocols for provider, tools, memory, planner, reflector, reviewer
- Naming freeze for the public surface

**Exit criteria**

- [x] Typed models + serialization tests
- [x] Contracts documented under `docs/`
- [x] Invalid action examples rejected by validators

---

## Phase 2 — Config, budgets, and policy

**Status:** Done  
**Branch:** `feat/config-policy`

**Goals**

- Layered config (defaults → file → env → CLI)
- Budgets: max steps, timeouts, cost caps
- Permission engine + path allow/deny rules + risk classes

**Exit criteria**

- [x] Config schema + examples in `configs/`
- [x] Policy unit tests (allow/deny matrices)
- [x] Docs for profiles (read-only vs standard vs strict)

---

## Phase 3 — Model provider adapters

**Status:** Done  
**Branch:** `feat/model-providers`

**Goals**

- Provider port for chat / structured decisions
- OpenAI-compatible reference adapter
- Deterministic stub provider for tests

**Exit criteria**

- [x] Provider protocol + reference + stub
- [x] Normalized responses (incl. error mapping)
- [x] Docs for adding a provider

---

## Phase 4 — Tool system + read-only repo tools

**Status:** Done  
**Branch:** `feat/tools-readonly`

**Goals**

- Tool registry, manifests, validation, executor
- Built-ins: list structure, search, read file
- Enforce workspace jail

**Exit criteria**

- [x] Registry + executor tests
- [x] Read-only tools on fixture repos
- [x] Path escape attempts denied

---

## Phase 5 — Memory system

**Status:** Done  
**Branch:** `feat/memory`

**Goals**

- Working memory for task/plan/actions/observations
- Long-term memory interfaces (repo knowledge, strategies)
- Budget-aware retrieval into model context

**Exit criteria**

- [x] In-memory working store + persistence hook
- [x] Long-term port + simple local backend
- [x] Tests for retention / summary-only reflection storage

---

## Phase 6 — Orchestrator + state machine (read-only autonomy)

**Status:** Done  
**Branch:** `feat/orchestrator`

**Goals**

- First real agent loop over the state machine
- Read-only profiles: analyze repo + answer/explain tasks
- Budgets and illegal transition handling

**Exit criteria**

- [x] Orchestrator drives Analyzing → … → Reporting for explain tasks
- [x] Stub-LLM end-to-end test
- [x] Serializable `RunState` resume smoke test

---

## Phase 7 — Planner + reflection

**Status:** Active  
**Branch:** `feat/plan-reflect`

**Goals**

- Structured `ExecutionPlan` creation and revision
- Reflection summaries after significant actions
- Never persist private chain-of-thought

**Exit criteria**

- [x] Planner + reflector ports and default implementations
- [x] Plan revision on reflection signals
- [x] Docs + tests for summary-only memory writes

---

## Phase 8 — Write tools + autonomous test loop

**Status:** Done  
**Branch:** `feat/edit-test-loop`

**Goals**

- Edit/write tools under policy
- Test runner tool + failure analysis loop
- Repair iterations with hard caps

**Exit criteria**

- [x] Fixture repo: agent fixes a seeded failing test
- [x] Write path denylist enforced
- [x] Loop terminates on success, deny, or budget

---

## Phase 9 — Reviewer + engineering report

**Status:** Planned  
**Branch:** `phase-9/review-report`

**Goals**

- Separate reviewer pass on diffs
- Final `EngineeringReport` artifact
- Standard profile requires review before success

**Exit criteria**

- [ ] `ReviewReport` schema + stub/real reviewer
- [ ] Report builder output stable enough for golden tests
- [ ] Findings can force return to Acting/Testing

---

## Phase 10 — Observability and replay

**Status:** Planned  
**Branch:** `phase-10/observability`

**Goals**

- Structured traces for steps, tools, approvals
- Console/JSON sinks
- Replay a run from trace for debugging

**Exit criteria**

- [ ] Trace event model + export
- [ ] Docs: interpreting a run
- [ ] Replay smoke test

---

## Phase 11 — CLI product surface

**Status:** Planned  
**Branch:** `phase-11/cli`

**Goals**

- `forgemind` CLI: run task, show status, validate config
- Human-friendly and machine-readable output

**Exit criteria**

- [ ] Entrypoint wired in packaging
- [ ] Help/version/run smoke tests
- [ ] Usage docs

---

## Phase 12 — Approval gates + git tools

**Status:** Planned  
**Branch:** `phase-12/approvals-git`

**Goals**

- Approval gate UX (CLI prompt + non-interactive policy)
- Git tools: status, diff, commit preparation
- Risky git mutation requires approval

**Exit criteria**

- [ ] Approval blocks/resumes runs correctly
- [ ] Git read tools + gated commit prep
- [ ] Safety tests for denied mutations

---

## Phase 13 — GitHub integration

**Status:** Planned  
**Branch:** `phase-13/github`

**Goals**

- Read issues / PR metadata
- Draft PR bodies and review comments via tools
- All remote mutations gated

**Exit criteria**

- [ ] GitHub tool pack behind permissions
- [ ] Draft-only default profile
- [ ] Integration tests with recorded HTTP fixtures

---

## Phase 14 — Plugins, evals, hardening, release

**Status:** Planned  
**Branch:** `phase-14/release-ready`

**Goals**

- Plugin entry points for external tool packs
- Eval harness on golden ASE scenarios
- Security pass, versioning, changelog discipline
- First tagged pre-release

**Exit criteria**

- [ ] Plugin loader + example plugin
- [ ] CI-friendly eval suite (stub/recorded)
- [ ] Release checklist + `0.1.0rc1` (or similar) ready

---

## Phase independence rules

1. One phase → one branch / PR train  
2. No forward dependencies on unfinished later APIs  
3. Docs + ADR updates travel with behavior changes  
4. Mutation capabilities do not land before Phase 8  
5. Update this file’s checkboxes when exit criteria move  

## Tracking

Detailed design: [`docs/architecture/PROPOSAL.md`](docs/architecture/PROPOSAL.md)  
Decisions: [`docs/adr/`](docs/adr/)
