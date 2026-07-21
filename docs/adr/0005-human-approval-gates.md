# ADR 0005: Human approval for risky operations

- **Status:** Accepted
- **Date:** 2026-07-20
- **Deciders:** ForgeMind maintainers

## Context

Autonomous edits are useful; autonomous git/GitHub mutation and destructive changes are dangerous.

## Decision

Introduce an **Approval Gate** in the runtime:

- Risk classes classify tools/actions (`read`, `write`, `exec`, `mutate_git`, `mutate_remote`, …)
- High-risk actions transition the run to `AwaitingApproval`
- Humans approve/deny via CLI/API/policy hooks
- Denials abort or re-plan; they never silently proceed

Default high-risk examples: commit, push, PR create, delete-heavy ops, lockfile changes (configurable).

## Consequences

### Positive

- Safer demos and real usage
- Clear enterprise/open-source trust story
- Auditable decision points

### Negative / trade-offs

- Less “fully hands-off” by default
- UX complexity for approval channels

## Alternatives considered

- Fully autonomous including push (rejected for default profiles)
- Always-on human approval for every edit (too slow; allowed as strict profile)
