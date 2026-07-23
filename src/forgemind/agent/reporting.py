"""Build an EngineeringReport from run state and memory."""

from __future__ import annotations

from forgemind.core.enums import RunStatus
from forgemind.core.memory import WorkingMemory
from forgemind.core.report import EngineeringReport
from forgemind.core.state import RunState


def build_engineering_report(
    state: RunState,
    working: WorkingMemory,
    *,
    finish_summary: str | None = None,
) -> EngineeringReport:
    """Assemble the final report for a completed/failed/aborted run."""

    findings = [obs.summary for obs in working.observations[-10:]]
    if finish_summary:
        findings.insert(0, finish_summary)
    if working.reflections:
        findings.append(f"Last reflection: {working.reflections[-1].learned}")

    follow_ups: list[str] = []
    if state.status == RunStatus.FAILED and state.last_error:
        follow_ups.append(f"Investigate failure: {state.last_error}")
    if working.blockers:
        follow_ups.extend(working.blockers[-5:])

    return EngineeringReport(
        run_id=state.run_id,
        status=state.status,
        task_restatement=state.task.goal,
        plan=state.plan or working.plan,
        key_findings=findings,
        residual_risks=list(working.blockers[-5:]),
        follow_ups=follow_ups,
        metadata={
            "files_inspected": list(working.files_inspected),
            "steps_used": state.budgets.steps_used,
            "tool_calls_used": state.budgets.tool_calls_used,
            "mode": state.task.mode.value,
        },
    )
