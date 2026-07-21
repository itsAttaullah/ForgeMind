"""Smoke tests for repository bootstrap (Phase 0)."""

from __future__ import annotations

import forgemind


def test_package_importable() -> None:
    assert forgemind.__version__ == "0.0.0"


def test_version_fixture(forgemind_version: str) -> None:
    assert forgemind_version == "0.0.0"


def test_public_export_surface() -> None:
    assert "__version__" in forgemind.__all__
