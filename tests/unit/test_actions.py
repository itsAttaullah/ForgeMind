"""Unit tests for AgentAction parsing and rejection of invalid payloads."""

from __future__ import annotations

import pytest

from forgemind.core import (
    ExecutionPlan,
    FinishAction,
    InvalidActionError,
    InvokeToolAction,
    PlanStep,
    parse_agent_action,
)


def test_parse_invoke_tool_action() -> None:
    action = parse_agent_action(
        {
            "type": "invoke_tool",
            "tool_name": "repo.read_file",
            "arguments": {"path": "README.md"},
            "rationale": "Need project overview",
        }
    )
    assert isinstance(action, InvokeToolAction)
    assert action.tool_name == "repo.read_file"
    assert action.arguments["path"] == "README.md"


def test_parse_finish_action_round_trip() -> None:
    original = FinishAction(summary="Task complete", success=True)
    restored = parse_agent_action(original.model_dump())
    assert isinstance(restored, FinishAction)
    assert restored.summary == "Task complete"


def test_parse_revise_plan_action() -> None:
    action = parse_agent_action(
        {
            "type": "revise_plan",
            "reason": "Auth already exists; focus on JWT wiring",
            "plan": {
                "summary": "Wire JWT into existing auth",
                "steps": [
                    {
                        "id": "inspect",
                        "title": "Inspect auth module",
                        "success_criteria": ["entrypoints identified"],
                    }
                ],
            },
        }
    )
    assert action.type == "revise_plan"
    assert isinstance(action.plan, ExecutionPlan)
    assert isinstance(action.plan.steps[0], PlanStep)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"type": "unknown_action"},
        {"type": "invoke_tool"},  # missing tool_name
        {"type": "invoke_tool", "tool_name": ""},
        {"type": "finish", "summary": ""},
        {"type": "abort"},  # missing reason
        {"type": "revise_plan", "reason": "x", "plan": {"summary": "s", "steps": []}},
        {"tool_name": "repo.read_file", "arguments": {}},  # missing discriminator
    ],
)
def test_invalid_actions_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(InvalidActionError):
        parse_agent_action(payload)  # type: ignore[arg-type]


def test_extra_fields_forbidden() -> None:
    with pytest.raises(InvalidActionError):
        parse_agent_action(
            {
                "type": "finish",
                "summary": "done",
                "secret_cot": "should not be accepted",
            }
        )
