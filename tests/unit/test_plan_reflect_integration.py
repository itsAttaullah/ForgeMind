"""Orchestrator integration with planner/reflector plan revision."""

from __future__ import annotations

import asyncio
from pathlib import Path

from forgemind.agent import ScriptedActionSelector, create_readonly_orchestrator, explain_task
from forgemind.config import AgentProfile, profile_config
from forgemind.core.enums import RunStatus

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "sample_repo"


def test_denied_read_triggers_plan_revision_event() -> None:
    config = profile_config(AgentProfile.READONLY)
    actor = ScriptedActionSelector(
        [
            {
                "type": "invoke_tool",
                "tool_name": "repo.read_file",
                "arguments": {"path": ".env"},
            },
            {
                "type": "finish",
                "summary": "Avoided secrets and finished",
                "success": True,
            },
        ]
    )
    orch = create_readonly_orchestrator(
        workspace_root=FIXTURE_ROOT,
        config=config,
        actor=actor,
    )
    result = asyncio.run(orch.run(explain_task(FIXTURE_ROOT, "Explain secrets handling")))
    assert result.state.status == RunStatus.COMPLETED
    assert result.state.plan is not None
    kinds = [event["kind"] for event in result.events]
    assert "reflection" in kinds
    assert "plan_revised" in kinds
    assert int(result.state.plan.metadata.get("revision_count", 0)) >= 1
