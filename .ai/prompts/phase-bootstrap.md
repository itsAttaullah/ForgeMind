# Prompt: work a ForgeMind phase

Use this template when asking a coding agent to implement a phase.

```text
You are working on ForgeMind, an open-source agent runtime.

Constraints:
- Follow ROADMAP.md and .ai/PHASES.md
- Do not implement phases beyond the target phase
- Do not build the agent loop before Phase 6
- Do not commit or push unless I explicitly ask
- Keep changes scoped, typed, lint-clean, and tested
- Update docs/ROADMAP exit criteria when appropriate

Target phase: Phase <N> — <name>
Goals:
- <goal 1>
- <goal 2>

Out of scope:
- <item>

Please:
1. Read relevant docs in docs/engineering/ and .ai/
2. Implement only what this phase requires
3. Add tests
4. Summarize what changed and how to verify
```
