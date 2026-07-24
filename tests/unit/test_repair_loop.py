"""Phase 8 mutable orchestrator: write/edit + test repair loop."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

from forgemind.agent import (
    ScriptedActionSelector,
    create_mutable_orchestrator,
    create_readonly_orchestrator,
    explain_task,
    fix_task,
)
from forgemind.config import AgentProfile, profile_config
from forgemind.config.models import BudgetSettings
from forgemind.core.enums import RunStatus

REPAIR_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "repair_repo"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    dest = tmp_path / "repair_repo"
    shutil.copytree(REPAIR_ROOT, dest, ignore=shutil.ignore_patterns(".env"))
    (dest / ".env").write_text("SECRET=1\n", encoding="utf-8")
    return dest


def test_scripted_fix_loop_passes_seeded_tests(workspace: Path) -> None:
    config = profile_config(AgentProfile.STANDARD)
    actor = ScriptedActionSelector(
        [
            {
                "type": "invoke_tool",
                "tool_name": "repo.read_file",
                "arguments": {"path": "calc.py"},
            },
            {
                "type": "invoke_tool",
                "tool_name": "repo.edit_file",
                "arguments": {
                    "path": "calc.py",
                    "old_string": "return left + right + 1",
                    "new_string": "return left + right",
                },
            },
            {"type": "run_tests", "selector": "test_calc.py"},
            {
                "type": "finish",
                "summary": "Fixed calc.add so tests pass",
                "success": True,
            },
        ]
    )
    orch = create_mutable_orchestrator(
        workspace_root=workspace,
        config=config,
        actor=actor,
    )
    result = asyncio.run(orch.run(fix_task(workspace, "Fix failing calc tests")))
    assert result.state.status == RunStatus.COMPLETED
    assert result.report is not None
    assert any(
        e["kind"] == "test_result" and e["payload"].get("passed") is True
        for e in result.events
    )
    assert "return left + right + 1" not in (workspace / "calc.py").read_text(
        encoding="utf-8"
    )


def test_write_deny_terminates_run(workspace: Path) -> None:
    config = profile_config(AgentProfile.STANDARD)
    actor = ScriptedActionSelector(
        [
            {
                "type": "invoke_tool",
                "tool_name": "repo.write_file",
                "arguments": {"path": ".env", "content": "SECRET=leaked\n"},
            },
            {
                "type": "finish",
                "summary": "should not reach",
                "success": True,
            },
        ]
    )
    orch = create_mutable_orchestrator(
        workspace_root=workspace,
        config=config,
        actor=actor,
    )
    result = asyncio.run(orch.run(fix_task(workspace, "Do not write secrets")))
    assert result.state.status == RunStatus.FAILED
    assert result.state.last_error is not None
    assert "denylist" in result.state.last_error


def test_repair_budget_terminates_loop(workspace: Path) -> None:
    config = profile_config(AgentProfile.STANDARD).model_copy(
        update={
            "budgets": BudgetSettings(
                max_steps=20,
                max_tool_calls=50,
                max_repair_iterations=1,
                timeout_seconds=900.0,
            )
        }
    )
    actor = ScriptedActionSelector(
        [
            {"type": "run_tests", "selector": "test_calc.py"},
            {"type": "run_tests", "selector": "test_calc.py"},
            {
                "type": "finish",
                "summary": "should not reach",
                "success": True,
            },
        ]
    )
    orch = create_mutable_orchestrator(
        workspace_root=workspace,
        config=config,
        actor=actor,
    )
    result = asyncio.run(orch.run(fix_task(workspace, "Keep failing")))
    assert result.state.status == RunStatus.FAILED
    assert result.state.last_error is not None
    assert "repair budget" in result.state.last_error
    assert result.state.budgets.repair_iterations_used >= 1


def test_readonly_blocks_write_tools(workspace: Path) -> None:
    config = profile_config(AgentProfile.READONLY)
    actor = ScriptedActionSelector(
        [
            {
                "type": "invoke_tool",
                "tool_name": "repo.write_file",
                "arguments": {"path": "hack.py", "content": "x=1\n"},
            },
            {
                "type": "finish",
                "summary": "blocked write then finished",
                "success": True,
            },
        ]
    )
    orch = create_readonly_orchestrator(
        workspace_root=workspace,
        config=config,
        actor=actor,
    )
    result = asyncio.run(orch.run(explain_task(workspace, "Attempt write in readonly")))
    assert result.state.status == RunStatus.COMPLETED
    assert not (workspace / "hack.py").exists()
