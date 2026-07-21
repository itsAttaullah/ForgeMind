"""Shared pytest fixtures for ForgeMind."""

from __future__ import annotations

import pytest


@pytest.fixture
def forgemind_version() -> str:
    """Return the packaged library version string."""
    from forgemind import __version__

    return __version__
