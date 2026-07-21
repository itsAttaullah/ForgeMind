# ForgeMind

**ForgeMind** is an open-source **Autonomous Software Engineering Agent** — a system that behaves like a software engineer, not a chatbot.

Given a task (“fix this bug”, “add this feature”, “review this code”), ForgeMind plans, inspects the repository, uses tools, edits under policy, runs tests, reflects, self-reviews, and produces an engineering report.

The LLM **decides** the next action. The runtime **controls** tools, permissions, state, memory, and safety. The model never touches the filesystem or shell directly.

This repository is under phased development. The agent itself is **not** implemented yet. See [`ROADMAP.md`](ROADMAP.md) and the [architecture proposal](docs/architecture/PROPOSAL.md).

## Status

| Item | State |
|------|--------|
| Repository bootstrap | Phase 0 complete |
| Architecture proposal | Drafted |
| Agent runtime | Not started |
| Public API | Not frozen |
| Stable release | Not yet |

## What this project will become

- Explicit run state machine and orchestrator
- Planning, reflection, and a separate reviewer role
- Modular tool plugins (repo, edit, test, git, GitHub)
- Working + long-term memory (summaries only — no private CoT)
- Autonomous test-repair loops with budgets
- Human approval gates for risky operations
- Final engineering reports and inspectable traces

Until roadmap phases land, treat package modules as scaffolding only.

## Repository layout

```text
ForgeMind/
├── .ai/                  # Guidance for humans and coding agents
├── docs/                 # Engineering and product documentation
├── src/forgemind/        # Library source (src layout)
├── tests/                # Pytest suite
├── examples/             # Usage examples (added as phases land)
├── configs/              # Example configuration files
├── scripts/              # Developer utility scripts
├── ROADMAP.md            # 15-phase development plan
├── CONTRIBUTING.md       # How to contribute
└── pyproject.toml        # Package, test, and lint configuration
```

## Requirements

- Python **3.11+**
- A virtual environment (recommended)

## Quick start (development)

```bash
# Clone
git clone https://github.com/<org>/forgemind.git
cd forgemind

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install in editable mode with dev tools
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff check .
ruff format .
mypy src
```

## Documentation

- [Architecture proposal](docs/architecture/PROPOSAL.md) — system design
- [ADRs](docs/adr/README.md) — architecture decisions
- [Roadmap](ROADMAP.md) — phase-by-phase plan
- [Contributing](CONTRIBUTING.md) — contribution workflow
- [Engineering overview](docs/engineering/overview.md) — how this repo is developed
- [Development process](docs/engineering/development-process.md)
- [Architecture principles](docs/engineering/architecture-principles.md)
- [Phase workflow](docs/engineering/phase-workflow.md)
- [Testing strategy](docs/engineering/testing-strategy.md)

## Design principles (preview)

1. **LLM decides; runtime controls** — agency inside hard boundaries (ADR 0001).
2. **Tool-mediated side effects only** — no raw FS/shell from the model (ADR 0002).
3. **Explicit run state** — durable state machine, not chat-as-control-flow (ADR 0003).
4. **Separate reviewer role** — author ≠ reviewer (ADR 0004).
5. **Human approval for risk** — commits, pushes, remote mutations gated (ADR 0005).
6. **Framework independence** — first-party orchestrator; no LangChain core (ADR 0006).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Please open issues against a specific roadmap phase when possible.

## License

[MIT](LICENSE) © 2026 ForgeMind Contributors
