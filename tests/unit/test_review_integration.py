"""Phase 9 orchestrator review integration."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import pytest

from forgemind.agent import (
    ScriptedActionSelector,
    create_mutable_orchestrator,
    fix_task,
)
from forgemind.config import AgentProfile, profile_config
from forgemind.core.enums import FindingSeverity, RunStatus
from forgemind.core.memory import MemorySnapshot
from forgemind.core.review import ReviewFinding, ReviewReport
from forgemind.core.state import RunState

REPAIR_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "repair_repo"


class StubBlockingReviewer:
    async def review(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        diff_summary: str,
        focus: list[str] | None = None,
    ) -> ReviewReport:
        return ReviewReport(
            summary="Blocking findings present",
            findings=[
                ReviewFinding(
                    title="Missing edge-case coverage",
                    severity=FindingSeverity.HIGH,
                    detail="Need another test for negatives.",
                    recommendation="Return to acting and add coverage.",
                )
            ],
            approve_completion=False,
        )


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    dest = tmp_path / "repair_repo"
    shutil.copytree(REPAIR_ROOT, dest, ignore=shutil.ignore_patterns(".env"))
    return dest


def test_fix_loop_auto_reviews_before_completion(workspace: Path) -> None:
    config = profile_config(AgentProfile.STANDARD)
    assert config.require_review_before_completion is True
    actor = ScriptedActionSelector(
        [
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
    assert result.report.review is not None
    assert result.report.review.approve_completion is True
    assert any(e["kind"] == "review" for e in result.events)


def test_blocking_review_returns_to_acting(workspace: Path) -> None:
    config = profile_config(AgentProfile.STANDARD)
    actor = ScriptedActionSelector(
        [
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
            {"type": "request_review", "focus": ["edge cases"]},
            {
                "type": "finish",
                "summary": "should not complete after blocking review",
                "success": True,
            },
            {
                "type": "finish",
                "summary": "still blocked without new review approval",
                "success": True,
            },
            {"type": "abort", "reason": "stop after blocked review"},
        ]
    )
    orch = create_mutable_orchestrator(
        workspace_root=workspace,
        config=config,
        actor=actor,
        reviewer=StubBlockingReviewer(),
    )
    result = asyncio.run(orch.run(fix_task(workspace, "Fix and review")))
    assert result.state.status == RunStatus.ABORTED
    assert any(e["kind"] == "review" for e in result.events)
    assert any(e["kind"] == "review_blocked_finish" for e in result.events)
    kinds = [e["kind"] for e in result.events]
    assert kinds.count("review_blocked_finish") >= 1
