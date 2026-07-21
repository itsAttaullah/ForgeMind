"""Validation helpers for LLM / JSON action payloads."""

from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter
from pydantic import ValidationError as PydanticValidationError

from forgemind.core.actions import AgentAction
from forgemind.core.errors import InvalidActionError

_ACTION_ADAPTER: TypeAdapter[AgentAction] = TypeAdapter(AgentAction)

__all__ = [
    "action_type_name",
    "parse_agent_action",
    "validate_agent_action",
]


def parse_agent_action(payload: dict[str, Any] | AgentAction) -> AgentAction:
    """Parse and validate an agent action from a mapping or model instance.

    Raises:
        InvalidActionError: If the payload is not a supported ``AgentAction``.
    """

    try:
        return _ACTION_ADAPTER.validate_python(payload)
    except PydanticValidationError as exc:
        raise InvalidActionError(_format_validation_error(exc)) from exc


def validate_agent_action(payload: dict[str, Any] | AgentAction) -> AgentAction:
    """Alias for :func:`parse_agent_action` (explicit naming for call sites)."""

    return parse_agent_action(payload)


def action_type_name(action: AgentAction) -> str:
    """Return the discriminator string for a validated action."""

    return action.type


def _format_validation_error(exc: PydanticValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "invalid agent action"
    first = errors[0]
    loc = ".".join(str(part) for part in first.get("loc", ())) or "<root>"
    msg = first.get("msg", "invalid")
    return f"invalid agent action at {loc}: {msg}"
