"""Reviewer unit tests (Phase 9)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from forgemind.core.enums import RunStatus, TaskMode
from forgemind.core.memory import MemorySnapshot, WorkingMemory
from forgemind.core.state import RunState
from forgemind.core.task import TaskSpec
from forgemind.core.tools import Observation
from forgemind.review import (
    HeuristicReviewer,
    build_diff_summary,
    resume_status_after_review,
    should_block_completion,
)


def _state() -> RunState:
    return RunState(
        task=TaskSpec(
            goal="Fix calc",
            workspace_root=Path("."),
            mode=TaskMode.FIX,
        ),
        status=RunStatus.REVIEWING,
    )


def test_heuristic_blocks_failed_tests() -> None:
    memory = MemorySnapshot(
        working=WorkingMemory(
            test_summaries=["tests failed"],
            observations=[
                Observation(
                    source="tool:repo.edit_file",
                    summary="repo.edit_file succeeded",
                    details={"output": {"path": "calc.py"}},
                )
            ],
        )
    )
    report = asyncio.run(
        HeuristicReviewer().review(
            _state(),
            memory,
            diff_summary=build_diff_summary(memory.working),
        )
    )
    assert should_block_completion(report)
    assert report.has_blocking_findings
    assert resume_status_after_review(report, memory) == RunStatus.TESTING


def test_heuristic_approves_when_tests_pass() -> None:
    memory = MemorySnapshot(
        working=WorkingMemory(
            test_summaries=["tests passed"],
            observations=[
                Observation(
                    source="tool:repo.edit_file",
                    summary="repo.edit_file succeeded",
                    details={"output": {"path": "calc.py"}},
                )
            ],
        )
    )
    report = asyncio.run(
        HeuristicReviewer().review(
            _state(),
            memory,
            diff_summary=build_diff_summary(memory.working),
        )
    )
    assert report.approve_completion is True
    assert not should_block_completion(report)
