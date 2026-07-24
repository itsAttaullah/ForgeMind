"""Write/edit and test.run tool tests."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

from forgemind.config import AgentProfile, profile_config
from forgemind.core.enums import ToolResultStatus
from forgemind.tools import create_readonly_tooling, create_standard_tooling

REPAIR_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "repair_repo"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    dest = tmp_path / "repair_repo"
    shutil.copytree(REPAIR_ROOT, dest, ignore=shutil.ignore_patterns(".env"))
    (dest / ".env").write_text("SECRET=1\n", encoding="utf-8")
    return dest


@pytest.fixture
def tooling(workspace: Path):
    config = profile_config(AgentProfile.STANDARD)
    return create_standard_tooling(workspace_root=workspace, config=config)


def test_standard_tooling_registers_write_and_test(tooling) -> None:
    names = set(tooling.registry.names())
    assert "repo.write_file" in names
    assert "repo.edit_file" in names
    assert "test.run" in names
    assert "repo.read_file" in names


def test_write_file_creates_content(tooling, workspace: Path) -> None:
    result = asyncio.run(
        tooling.invoke(
            "repo.write_file",
            {"path": "notes.txt", "content": "hello\n"},
        )
    )
    assert result.status == ToolResultStatus.SUCCESS
    assert (workspace / "notes.txt").read_text(encoding="utf-8") == "hello\n"
    assert result.output["created"] is True


def test_edit_file_replaces_exact_string(tooling, workspace: Path) -> None:
    result = asyncio.run(
        tooling.invoke(
            "repo.edit_file",
            {
                "path": "calc.py",
                "old_string": "return left + right + 1",
                "new_string": "return left + right",
            },
        )
    )
    assert result.status == ToolResultStatus.SUCCESS
    assert result.output["replacements"] == 1
    text = (workspace / "calc.py").read_text(encoding="utf-8")
    assert "return left + right\n" in text
    assert "+ 1" not in text.split("return")[-1]


def test_write_denylist_blocks_env(tooling) -> None:
    result = asyncio.run(
        tooling.invoke(
            "repo.write_file",
            {"path": ".env", "content": "SECRET=leaked\n"},
        )
    )
    assert result.status == ToolResultStatus.DENIED
    assert "denylist" in (result.error or "")


def test_readonly_tooling_lacks_write_tools(workspace: Path) -> None:
    tooling = create_readonly_tooling(
        workspace_root=workspace,
        config=profile_config(AgentProfile.READONLY),
    )
    names = tooling.registry.names()
    assert "repo.write_file" not in names
    assert "test.run" not in names


def test_run_tests_fails_on_seeded_bug(tooling) -> None:
    result = asyncio.run(tooling.invoke("test.run", {"selector": "test_calc.py"}))
    assert result.status == ToolResultStatus.SUCCESS
    assert result.output["passed"] is False
    assert result.output["exit_code"] != 0


def test_run_tests_passes_after_fix(tooling, workspace: Path) -> None:
    edit = asyncio.run(
        tooling.invoke(
            "repo.edit_file",
            {
                "path": "calc.py",
                "old_string": "return left + right + 1",
                "new_string": "return left + right",
            },
        )
    )
    assert edit.status == ToolResultStatus.SUCCESS
    result = asyncio.run(tooling.invoke("test.run", {"selector": "test_calc.py"}))
    assert result.status == ToolResultStatus.SUCCESS
    assert result.output["passed"] is True
    assert "return left + right + 1" not in (workspace / "calc.py").read_text(
        encoding="utf-8"
    )
