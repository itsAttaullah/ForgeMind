"""Read-only repository tool tests against the sample fixture repo."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from forgemind.config import AgentProfile, profile_config
from forgemind.core.enums import ToolResultStatus
from forgemind.core.errors import PermissionDeniedError
from forgemind.tools import create_readonly_tooling
from forgemind.tools.repo.read_file import ReadFileTool

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "sample_repo"


@pytest.fixture
def tooling():
    config = profile_config(AgentProfile.READONLY)
    return create_readonly_tooling(workspace_root=FIXTURE_ROOT, config=config)


def test_list_structure(tooling) -> None:
    result = asyncio.run(tooling.invoke("repo.list_structure", {"path": ".", "max_depth": 3}))
    assert result.status == ToolResultStatus.SUCCESS
    paths = {entry["path"] for entry in result.output["entries"]}
    assert "README.md" in paths
    assert "src/app.py" in paths


def test_search_finds_marker(tooling) -> None:
    result = asyncio.run(tooling.invoke("repo.search", {"query": "JWT_AUTH_MARKER"}))
    assert result.status == ToolResultStatus.SUCCESS
    assert result.output["count"] >= 1
    assert any(match["path"] == "README.md" for match in result.output["matches"])


def test_read_file(tooling) -> None:
    result = asyncio.run(tooling.invoke("repo.read_file", {"path": "src/app.py"}))
    assert result.status == ToolResultStatus.SUCCESS
    assert "greet" in result.output["content"]
    assert result.output["path"] == "src/app.py"


def test_read_file_denies_env(tooling) -> None:
    result = asyncio.run(tooling.invoke("repo.read_file", {"path": ".env"}))
    assert result.status == ToolResultStatus.DENIED
    assert "denylist" in (result.error or "")


def test_path_escape_denied(tooling) -> None:
    outside = FIXTURE_ROOT.parent / "outside.txt"
    result = asyncio.run(tooling.invoke("repo.read_file", {"path": str(outside)}))
    assert result.status == ToolResultStatus.DENIED
    assert "escapes workspace" in (result.error or "")


def test_read_tool_direct_escape_raises() -> None:
    tool = ReadFileTool(FIXTURE_ROOT)
    outside = FIXTURE_ROOT.parent / "secret.txt"
    with pytest.raises(PermissionDeniedError):
        asyncio.run(tool.run({"path": str(outside)}))


def test_manifests_registered(tooling) -> None:
    names = tooling.registry.names()
    assert names == ["repo.list_structure", "repo.read_file", "repo.search"]
