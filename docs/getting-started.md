# Getting started

This guide covers the **bootstrap** repository only. The agent runtime is not implemented yet.

## Prerequisites

- Python 3.11 or newer
- `pip` and `venv`
- Git

## Install

```bash
git clone https://github.com/<org>/forgemind.git
cd forgemind
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install the package in editable mode with development extras:

```bash
pip install -e ".[dev]"
```

## Verify

```bash
python scripts/dev_info.py
pytest
ruff check .
mypy src
```

You should see `forgemind=0.0.0` and a passing smoke test suite.

## What to build next

Follow [`../ROADMAP.md`](../ROADMAP.md). Start with **Phase 1 — Core types and contracts**. Do not implement the agent loop until Phase 6.

## Further reading

- [Engineering overview](engineering/overview.md)
- [Contributing](../CONTRIBUTING.md)
- [`.ai` guidance](../.ai/README.md)
