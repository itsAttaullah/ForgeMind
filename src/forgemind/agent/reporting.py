"""Build an EngineeringReport from run state and memory."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from forgemind.core.enums import RunStatus
from forgemind.core.memory import WorkingMemory
from forgemind.core.report import EngineeringReport
from forgemind.core.state import RunState
from forgemind.review.diff import infer_changed_files


def build_engineering_report(
    state: RunState,
    working: WorkingMemory,
    *,
    finish_summary: str | None = None,
    created_at: datetime | None = None,
) -> EngineeringReport:
    """Assemble the final report for a completed/failed/aborted run."""

    findings = [obs.summary for obs in working.observations[-10:]]
    if finish_summary:
        findings.insert(0, finish_summary)
    if working.reflections:
        findings.append(f"Last reflection: {working.reflections[-1].learned}")
    if working.last_review is not None:
        findings.append(f"Review: {working.last_review.summary}")

    follow_ups: list[str] = []
    if state.status == RunStatus.FAILED and state.last_error:
        follow_ups.append(f"Investigate failure: {state.last_error}")
    if working.blockers:
        follow_ups.extend(working.blockers[-5:])
    if working.last_review is not None:
        for finding in working.last_review.findings:
            if finding.recommendation:
                follow_ups.append(finding.recommendation)

    residual = list(working.blockers[-5:])
    if working.last_review is not None and working.last_review.has_blocking_findings:
        residual.extend(
            f"{finding.severity.value}: {finding.title}"
            for finding in working.last_review.findings
            if finding.severity.value in {"high", "critical"}
        )

    changes = infer_changed_files(working)
    tests_run = list(working.test_summaries)
    test_results_summary = None
    if tests_run:
        passed = sum(1 for item in tests_run if "pass" in item.lower())
        failed = sum(1 for item in tests_run if "fail" in item.lower())
        test_results_summary = f"{passed} passed entries, {failed} failed entries"

    kwargs: dict[str, Any] = {
        "run_id": state.run_id,
        "status": state.status,
        "task_restatement": state.task.goal,
        "plan": state.plan or working.plan,
        "key_findings": findings,
        "changes": changes,
        "tests_run": tests_run,
        "test_results_summary": test_results_summary,
        "review": working.last_review,
        "residual_risks": residual,
        "follow_ups": follow_ups,
        "metadata": {
            "files_inspected": list(working.files_inspected),
            "steps_used": state.budgets.steps_used,
            "tool_calls_used": state.budgets.tool_calls_used,
            "mode": state.task.mode.value,
        },
    }
    if created_at is not None:
        kwargs["created_at"] = created_at
    return EngineeringReport(**kwargs)


def report_dict_for_golden(report: EngineeringReport) -> dict[str, Any]:
    """Serialize a report for golden comparisons (stable, no timestamps)."""

    data = report.model_dump(mode="json")
    data.pop("created_at", None)
    if isinstance(data.get("plan"), dict):
        data["plan"].pop("created_at", None)
    return data
