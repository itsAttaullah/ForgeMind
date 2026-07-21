# ADR 0004: Separate reviewer role

- **Status:** Accepted
- **Date:** 2026-07-20
- **Deciders:** ForgeMind maintainers

## Context

Agents that “self-check” in the same turn that produced code often rubber-stamp their own work.

## Decision

ForgeMind includes a **distinct Reviewer role/pass**:

- Runs after validation (typically post-testing)
- Consumes diff + task + test results
- Emits a structured `ReviewReport` (bugs, security, edge cases, regressions)
- May force return to Acting/Testing

Implementation may use the same provider with a different profile/prompt, or a different model. It must not be merely “please double-check” appended to the actor prompt in the same step.

## Consequences

### Positive

- Higher chance of catching issues
- Cleaner reports for humans
- Aligns with real engineering practice (author ≠ reviewer)

### Negative / trade-offs

- Extra latency/cost per run
- Need careful anti-sycophancy prompting and structured findings

## Alternatives considered

- Single-pass actor self-check (rejected as primary quality gate)
- External-only human review (still supported, but not a substitute for automated self-review)
