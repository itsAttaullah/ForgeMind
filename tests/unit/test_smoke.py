"""Smoke tests for repository bootstrap / package surface."""

from __future__ import annotations

import forgemind


def test_package_importable() -> None:
    assert forgemind.__version__ == "0.1.0.dev0"


def test_version_fixture(forgemind_version: str) -> None:
    assert forgemind_version == "0.1.0.dev0"


def test_public_export_surface() -> None:
    assert "__version__" in forgemind.__all__
    assert "TaskSpec" in forgemind.__all__
    assert "parse_agent_action" in forgemind.__all__
