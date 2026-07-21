"""Normalize vendor payloads into ForgeMind provider contracts."""

from __future__ import annotations

import json
from typing import Any

from forgemind.core.enums import MessageRole
from forgemind.core.errors import ProviderError
from forgemind.core.messages import ChatMessage
from forgemind.core.provider import ProviderResponse


def normalize_openai_chat_completion(payload: dict[str, Any]) -> ProviderResponse:
    """Map an OpenAI-compatible ``/chat/completions`` JSON body to ``ProviderResponse``."""

    try:
        choices = payload["choices"]
        first = choices[0]
        message = first["message"]
        role = MessageRole(str(message["role"]))
        content = message.get("content") or ""
        if not isinstance(content, str):
            content = json.dumps(content)
        assistant = ChatMessage(
            role=role,
            content=content,
            name=message.get("name"),
            tool_call_id=message.get("tool_call_id"),
        )
        usage_raw = payload.get("usage") or {}
        usage = {
            key: int(value) for key, value in usage_raw.items() if isinstance(value, (int, float))
        }
        return ProviderResponse(
            message=assistant,
            model=payload.get("model"),
            finish_reason=first.get("finish_reason"),
            usage=usage,
            raw=payload,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderError(f"invalid OpenAI-compatible response shape: {exc}") from exc


def decode_json_response(body: bytes) -> dict[str, Any]:
    """Decode a JSON HTTP body or raise ``ProviderError``."""

    try:
        loaded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderError(f"provider returned non-JSON body: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ProviderError("provider JSON root must be an object")
    return loaded
