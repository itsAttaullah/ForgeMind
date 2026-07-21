# Phase workflow

ForgeMind is delivered as **15 independent phases**. This document defines how a phase is opened, executed, and closed.

## Phase lifecycle

```text
Proposed → Active → In review → Done → (Maintained)
```

1. **Proposed** — listed in `ROADMAP.md` with goals and exit criteria
2. **Active** — a maintainer marks status Active; issues are tagged `phase-N`
3. **In review** — implementation PRs open; exit criteria nearly met
4. **Done** — exit criteria checked; status set to Done
5. **Maintained** — bugfixes allowed; feature expansion belongs to later phases

## Independence rules

| Rule | Meaning |
|------|---------|
| No forward deps | Phase N must not call APIs introduced only in Phase N+k |
| Coherent slice | Prefer vertical slices (types + tests + docs) over incomplete horizontal sprawl |
| One concern train | Avoid mixing Phase 4 tools and Phase 9 CLI in the same PR |
| Stable seams | If Phase N needs a hook for Phase N+k, add a minimal protocol/stub, not a full feature |

## Starting a phase

1. Confirm prior required phases are Done (or explicitly waived)
2. Set roadmap status to Active
3. Create tracking issues for exit criteria
4. Sketch public types/interfaces first when the phase introduces contracts

## During a phase

- Keep a short “out of scope” list in the PR body
- Add tests before expanding surface area
- Update `.ai/PHASES.md` notes if agent guidance needs clarifying
- Do not implement the agent loop before Phase 6

## Closing a phase

Checklist:

- [ ] All exit criteria in `ROADMAP.md` checked
- [ ] `docs/` updated
- [ ] Smoke / unit / relevant integration tests green
- [ ] No unexplained TODOs that block the next phase
- [ ] Changelog note prepared once changelogs exist (Phase 14)

## Cross-cutting work

Security fixes, dependency bumps, and doc typo fixes may land outside a phase. Label them clearly. If they change architecture, add an engineering note.

## Phase map (quick)

| Phase | Focus |
|------:|-------|
| 0 | Repository foundation + architecture |
| 1 | Core types and contracts |
| 2 | Config, budgets, policy |
| 3 | Providers |
| 4 | Tools (read-only repo) |
| 5 | Memory |
| 6 | Orchestrator (read-only autonomy) |
| 7 | Planner + reflection |
| 8 | Write tools + test loop |
| 9 | Reviewer + engineering report |
| 10 | Observability & replay |
| 11 | CLI |
| 12 | Approvals + git |
| 13 | GitHub |
| 14 | Plugins, evals, hardening |

Full detail: [`../../ROADMAP.md`](../../ROADMAP.md)  
Architecture: [`../architecture/PROPOSAL.md`](../architecture/PROPOSAL.md)
