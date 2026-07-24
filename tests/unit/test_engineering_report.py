"""Engineering report builder + golden stability tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from forgemind.agent.reporting import build_engineering_report, report_dict_for_golden
from forgemind.core.enums import FindingSeverity, RunStatus, TaskMode
from forgemind.core.memory import WorkingMemory
from forgemind.core.review import ReviewFinding, ReviewReport
from forgemind.core.state import BudgetCounters, RunState
from forgemind.core.task import TaskSpec
from forgemind.core.tools import Observation


def test_build_engineering_report_includes_review_and_changes() -> None:
    state = RunState(
        run_id="run-golden-1",
        task=TaskSpec(
            goal="Fix calc.add",
            workspace_root=Path("."),
            mode=TaskMode.FIX,
        ),
        status=RunStatus.COMPLETED,
        budgets=BudgetCounters(steps_used=4, tool_calls_used=3),
    )
    working = WorkingMemory(
        task_brief="Fix calc.add",
        files_inspected=["calc.py"],
        observations=[
            Observation(
                source="tool:repo.edit_file",
                summary="repo.edit_file succeeded",
                details={"output": {"path": "calc.py", "replacements": 1}},
            )
        ],
        test_summaries=["tests passed"],
        last_review=ReviewReport(
            summary="Review approved with no blocking findings.",
            findings=[
                ReviewFinding(
                    title="Looks good",
                    severity=FindingSeverity.INFO,
                    detail="Tests passed after edit.",
                )
            ],
            approve_completion=True,
        ),
    )
    report = build_engineering_report(
        state,
        working,
        finish_summary="Fixed add()",
        created_at=datetime(2026, 7, 24, 12, 0, tzinfo=UTC),
    )
    assert report.review is not None
    assert report.review.approve_completion is True
    assert report.changes[0].path == "calc.py"
    assert report.tests_run == ["tests passed"]
    assert "Fixed add()" in report.key_findings

    golden = report_dict_for_golden(report)
    assert "created_at" not in golden
    assert golden["run_id"] == "run-golden-1"
    assert golden["changes"][0]["path"] == "calc.py"
    assert golden["review"]["approve_completion"] is True
