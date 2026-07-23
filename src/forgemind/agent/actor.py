"""Action selectors for the orchestrator (actor role)."""

from __future__ import annotations

import json
import re
from collections import deque
from typing import Any

from forgemind.core.actions import AgentAction
from forgemind.core.enums import MessageRole
from forgemind.core.errors import InvalidActionError, ProviderError
from forgemind.core.memory import MemorySnapshot
from forgemind.core.messages import ChatMessage
from forgemind.core.protocols import ModelProvider
from forgemind.core.provider import ProviderRequest
from forgemind.core.state import RunState
from forgemind.core.tools import ToolManifest
from forgemind.core.validation import parse_agent_action

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


class ScriptedActionSelector:
    """Deterministic actor that returns a queued list of actions."""

    def __init__(self, actions: list[AgentAction | dict[str, Any]]) -> None:
        self._queue: deque[AgentAction] = deque(parse_agent_action(action) for action in actions)

    async def select_action(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        available_tools: list[ToolManifest],
    ) -> AgentAction:
        if not self._queue:
            raise InvalidActionError("scripted actor has no remaining actions")
        return self._queue.popleft()


class ProviderActionSelector:
    """Ask a model provider for the next ``AgentAction`` as JSON."""

    def __init__(self, provider: ModelProvider, *, model: str | None = None) -> None:
        self._provider = provider
        self._model = model

    async def select_action(
        self,
        state: RunState,
        memory: MemorySnapshot,
        *,
        available_tools: list[ToolManifest],
    ) -> AgentAction:
        request = ProviderRequest(
            model=self._model,
            messages=[
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=(
                        "You are the ForgeMind actor. Reply with ONLY a JSON object "
                        "for the next AgentAction. Allowed types: invoke_tool, "
                        "revise_plan, request_approval, run_tests, request_review, "
                        "finish, abort. Do not include chain-of-thought."
                    ),
                ),
                ChatMessage(
                    role=MessageRole.USER,
                    content=json.dumps(
                        {
                            "run_id": state.run_id,
                            "status": state.status.value,
                            "goal": state.task.goal,
                            "mode": state.task.mode.value,
                            "plan": (state.plan.model_dump(mode="json") if state.plan else None),
                            "tools": [
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.parameters.model_dump(mode="json"),
                                }
                                for tool in available_tools
                            ],
                            "recent_observations": [
                                obs.model_dump(mode="json")
                                for obs in memory.working.observations[-5:]
                            ],
                            "files_inspected": memory.working.files_inspected[-20:],
                        },
                        default=str,
                    ),
                ),
            ],
            response_format={"type": "json_object"},
        )
        try:
            response = await self._provider.complete(request)
        except ProviderError:
            raise
        payload = _extract_json_object(response.message.content)
        return parse_agent_action(payload)


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
    raise InvalidActionError("provider did not return a JSON AgentAction object")
