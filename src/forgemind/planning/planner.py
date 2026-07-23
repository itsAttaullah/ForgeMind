"""Heuristic and provider-backed planners."""

from __future__ import annotations

import json
import re
from typing import Any

from forgemind.core.enums import MessageRole, TaskMode
from forgemind.core.errors import InvalidActionError, ProviderError
from forgemind.core.memory import MemorySnapshot
from forgemind.core.messages import ChatMessage
from forgemind.core.plan import ExecutionPlan, PlanStep
from forgemind.core.protocols import ModelProvider
from forgemind.core.provider import ProviderRequest
from forgemind.core.state import RunState

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class HeuristicPlanner:
    """Deterministic planner that builds mode-aware structured plans."""

    async def create_plan(self, state: RunState, memory: MemorySnapshot) -> ExecutionPlan:
        return _plan_for_mode(state, memory)

    async def revise_plan(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        reason: str,
    ) -> ExecutionPlan:
        base = state.plan or await self.create_plan(state, memory)
        files = memory.working.files_inspected[-8:]
        observations = [obs.summary for obs in memory.working.observations[-5:]]
        revised_steps = list(base.steps)
        if files or observations:
            revised_steps.append(
                PlanStep(
                    id=f"adapt-{len(revised_steps) + 1}",
                    title="Follow updated understanding",
                    description=reason,
                    success_criteria=["Address reflection feedback"],
                    suspected_paths=list(files),
                )
            )
        questions = list(base.open_questions)
        if reason and reason not in questions:
            questions.append(reason)
        return ExecutionPlan(
            summary=f"{base.summary} (revised)",
            steps=revised_steps,
            risks=list(base.risks),
            open_questions=questions,
            metadata={
                **dict(base.metadata),
                "revision_reason": reason,
                "revision_count": int(base.metadata.get("revision_count", 0)) + 1,
            },
        )


class ProviderPlanner:
    """Ask a model provider for a JSON ``ExecutionPlan``."""

    def __init__(self, provider: ModelProvider, *, model: str | None = None) -> None:
        self._provider = provider
        self._model = model
        self._fallback = HeuristicPlanner()

    async def create_plan(self, state: RunState, memory: MemorySnapshot) -> ExecutionPlan:
        prompt = {
            "goal": state.task.goal,
            "mode": state.task.mode.value,
            "files_inspected": memory.working.files_inspected[-20:],
            "observations": [obs.summary for obs in memory.working.observations[-5:]],
            "instruction": (
                "Return ONLY JSON for ExecutionPlan with keys: "
                "summary, steps[{id,title,description,success_criteria,suspected_paths}], "
                "risks, open_questions."
            ),
        }
        try:
            payload = await self._request_json(prompt)
            return ExecutionPlan.model_validate(payload)
        except (ProviderError, InvalidActionError, ValueError):
            return await self._fallback.create_plan(state, memory)

    async def revise_plan(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        reason: str,
    ) -> ExecutionPlan:
        prompt = {
            "goal": state.task.goal,
            "reason": reason,
            "current_plan": state.plan.model_dump(mode="json") if state.plan else None,
            "observations": [obs.summary for obs in memory.working.observations[-5:]],
            "instruction": "Return ONLY a revised ExecutionPlan JSON object.",
        }
        try:
            payload = await self._request_json(prompt)
            plan = ExecutionPlan.model_validate(payload)
            meta = dict(plan.metadata)
            meta["revision_reason"] = reason
            return plan.model_copy(update={"metadata": meta})
        except (ProviderError, InvalidActionError, ValueError):
            return await self._fallback.revise_plan(state, memory, reason=reason)

    async def _request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._provider.complete(
            ProviderRequest(
                model=self._model,
                messages=[
                    ChatMessage(
                        role=MessageRole.SYSTEM,
                        content=(
                            "You are the ForgeMind planner. Reply with ONLY a JSON "
                            "ExecutionPlan. No chain-of-thought."
                        ),
                    ),
                    ChatMessage(role=MessageRole.USER, content=json.dumps(payload, default=str)),
                ],
                response_format={"type": "json_object"},
            )
        )
        return _extract_json_object(response.message.content)


def _plan_for_mode(state: RunState, memory: MemorySnapshot) -> ExecutionPlan:
    goal = state.task.goal
    mode = state.task.mode
    files = list(memory.working.files_inspected[-5:])

    if mode == TaskMode.EXPLAIN:
        steps = [
            PlanStep(
                id="survey",
                title="Survey repository structure",
                description="List top-level layout and key modules.",
                success_criteria=["Structure summarized"],
            ),
            PlanStep(
                id="inspect",
                title="Inspect relevant files",
                description="Read or search files that explain the goal.",
                success_criteria=["Key files inspected"],
                suspected_paths=files,
            ),
            PlanStep(
                id="summarize",
                title="Summarize findings",
                description="Produce a clear explanation of the repository/task.",
                success_criteria=["Engineering report ready"],
            ),
        ]
        summary = f"Explain and document: {goal}"
    elif mode in {TaskMode.FIX, TaskMode.FEATURE}:
        steps = [
            PlanStep(
                id="reproduce",
                title="Understand current behavior",
                success_criteria=["Relevant code located"],
            ),
            PlanStep(
                id="design",
                title="Design minimal change",
                success_criteria=["Change scope identified"],
            ),
            PlanStep(
                id="validate",
                title="Validate with inspection/tests when available",
                success_criteria=["Confidence in approach recorded"],
            ),
        ]
        summary = f"Plan changes for: {goal}"
    else:
        steps = [
            PlanStep(
                id="investigate",
                title="Investigate the task",
                success_criteria=["Enough context gathered"],
                suspected_paths=files,
            ),
            PlanStep(
                id="conclude",
                title="Conclude with findings",
                success_criteria=["Report produced"],
            ),
        ]
        summary = f"Investigate: {goal}"

    return ExecutionPlan(
        summary=summary,
        steps=steps,
        risks=["Read-only mode cannot apply code mutations yet"]
        if mode in {TaskMode.FIX, TaskMode.FEATURE}
        else [],
        open_questions=[],
        metadata={"planner": "heuristic", "mode": mode.value},
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        loaded = json.loads(cleaned)
        if isinstance(loaded, dict):
            return loaded
    except json.JSONDecodeError:
        match = _JSON_OBJECT_RE.search(cleaned)
        if match:
            loaded = json.loads(match.group(0))
            if isinstance(loaded, dict):
                return loaded
    raise InvalidActionError("provider did not return a JSON ExecutionPlan object")
