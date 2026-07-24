"""Tiny calculator with a seeded bug for repair-loop tests."""


def add(left: int, right: int) -> int:
    """Return the sum of ``left`` and ``right``."""

    # Intentionally wrong — Phase 8 fixture expects agents to fix this.
    return left + right + 1
