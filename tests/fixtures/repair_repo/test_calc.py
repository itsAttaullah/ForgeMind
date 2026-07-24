"""Failing tests that the Phase 8 repair loop should make pass."""

from calc import add


def test_add_two_plus_two() -> None:
    assert add(2, 2) == 4


def test_add_zero() -> None:
    assert add(0, 5) == 5
