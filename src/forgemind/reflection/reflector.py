"""Heuristic and provider-backed reflectors (summary-only)."""

from __future__ import annotations

import json
import re
from typing import Any

from forgemind.core.enums import MessageRole, ReflectionVerdict
from forgemind.core.errors import InvalidActionError, ProviderError
from forgemind.core.memory import MemorySnapshot
from forgemind.core.messages import ChatMessage
from forgemind.core.protocols import ModelProvider
from forgemind.core.provider import ProviderRequest
from forgemind.core.reflection import ReflectionSummary
from forgemind.core.state import RunState
from forgemind.core.tools import Observation
from forgemind.memory.retention import sanitize_reflection

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class HeuristicReflector:
    """Rule-based reflector that never stores private chain-of-thought."""

    async def reflect(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        observation: Observation,
    ) -> ReflectionSummary:
        denied = "denied" in observation.summary.lower()
        failed = "failed" in observation.summary.lower()
        helped = not denied and not failed

        if denied:
            verdict = ReflectionVerdict.REVISE_PLAN
            learned = f"Access/policy blocked progress: {observation.summary}"
            adjustment = "Avoid denied paths; choose alternate repo files."
            hint = "Search or list structure before reading sensitive paths."
        elif failed:
            verdict = ReflectionVerdict.RETRY
            learned = f"Last action failed: {observation.summary}"
            adjustment = None
            hint = "Retry with corrected arguments or a different tool."
        elif len(memory.working.files_inspected) == 0 and observation.source.startswith(
            "tool:repo.list"
        ):
            verdict = ReflectionVerdict.CONTINUE
            learned = "Repository layout surveyed; ready to inspect files."
            adjustment = None
            hint = "Read README or search for keywords from the goal."
        elif observation.source.startswith("tool:") and helped:
            verdict = ReflectionVerdict.CONTINUE
            learned = observation.summary
            adjustment = None
            hint = "Continue investigating or finish if enough context exists."
        else:
            verdict = ReflectionVerdict.CONTINUE
            learned = observation.summary
            adjustment = None
            hint = None

        # If we keep failing the same way, escalate plan revision.
        recent = memory.working.observations[-3:]
        if len(recent) >= 3 and all("denied" in item.summary.lower() for item in recent):
            verdict = ReflectionVerdict.REVISE_PLAN
            adjustment = "Repeated denials — revise plan away from blocked resources."

        summary = ReflectionSummary(
            verdict=verdict,
            helped=helped,
            learned=learned,
            plan_adjustment=adjustment,
            next_hint=hint,
            metadata={"reflector": "heuristic"},
        )
        return sanitize_reflection(summary)


class ProviderReflector:
    """Ask a model for a JSON ReflectionSummary, then sanitize it."""

    def __init__(self, provider: ModelProvider, *, model: str | None = None) -> None:
        self._provider = provider
        self._model = model
        self._fallback = HeuristicReflector()

    async def reflect(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        observation: Observation,
    ) -> ReflectionSummary:
        prompt = {
            "goal": state.task.goal,
            "status": state.status.value,
            "observation": observation.model_dump(mode="json"),
            "instruction": (
                "Return ONLY JSON ReflectionSummary with keys: verdict, helped, "
                "learned, plan_adjustment, next_hint. verdict in "
                "[continue, retry, revise_plan, escalate, stop]. "
                "Do not include chain-of-thought."
            ),
        }
        try:
            payload = await self._request_json(prompt)
            summary = ReflectionSummary.model_validate(payload)
            return sanitize_reflection(summary)
        except (ProviderError, InvalidActionError, ValueError):
            return await self._fallback.reflect(state, memory, observation=observation)

    async def _request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._provider.complete(
            ProviderRequest(
                model=self._model,
                messages=[
                    ChatMessage(
                        role=MessageRole.SYSTEM,
                        content=(
                            "You are the ForgeMind reflector. Reply with ONLY a JSON "
                            "ReflectionSummary. Never include private reasoning."
                        ),
                    ),
                    ChatMessage(role=MessageRole.USER, content=json.dumps(payload, default=str)),
                ],
                response_format={"type": "json_object"},
            )
        )
        return _extract_json_object(response.message.content)


def should_revise_plan(reflection: ReflectionSummary) -> bool:
    """Return True when reflection indicates the plan should change."""

    return reflection.verdict == ReflectionVerdict.REVISE_PLAN


def observation_looks_significant(observation: Observation) -> bool:
    """Phase 7 treats tool/system outcomes as significant reflection triggers."""

    return observation.source.startswith(("tool:", "system"))


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
    raise InvalidActionError("provider did not return a JSON ReflectionSummary object")
