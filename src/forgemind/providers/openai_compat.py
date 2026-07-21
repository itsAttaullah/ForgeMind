"""OpenAI-compatible chat completion provider."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from typing import Any
from urllib.error import URLError

from forgemind.config.models import ProviderSettings
from forgemind.core.errors import ConfigurationError
from forgemind.core.provider import ProviderRequest, ProviderResponse
from forgemind.providers.errors import map_transport_error, raise_for_http_response
from forgemind.providers.http import HttpResponse, post_json
from forgemind.providers.normalize import decode_json_response, normalize_openai_chat_completion

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAICompatibleProvider:
    """Call an OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(
        self,
        *,
        settings: ProviderSettings,
        api_key: str | None = None,
        transport: Callable[..., HttpResponse] | None = None,
    ) -> None:
        self._settings = settings
        self._api_key = api_key
        self._transport = transport or post_json

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        return await asyncio.to_thread(self._complete_sync, request)

    def _complete_sync(self, request: ProviderRequest) -> ProviderResponse:
        api_key = self._resolve_api_key()
        url = f"{self._base_url().rstrip('/')}/chat/completions"
        payload = self._build_payload(request)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        try:
            response = self._transport(
                url,
                headers=headers,
                payload=payload,
                timeout_seconds=self._settings.timeout_seconds,
            )
        except URLError as exc:
            raise map_transport_error(exc, provider="openai_compatible") from exc

        raise_for_http_response(response, provider="openai_compatible")
        body = decode_json_response(response.body)
        return normalize_openai_chat_completion(body)

    def _resolve_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        env_name = self._settings.api_key_env
        value = os.environ.get(env_name)
        if not value or not value.strip():
            raise ConfigurationError(f"missing API key: set {env_name} or pass api_key explicitly")
        return value.strip()

    def _base_url(self) -> str:
        return self._settings.base_url or DEFAULT_OPENAI_BASE_URL

    def _build_payload(self, request: ProviderRequest) -> dict[str, Any]:
        model = request.model or self._settings.model
        if not model:
            raise ConfigurationError("provider model is required (config or request)")

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": message.role.value,
                    "content": message.content,
                    **({"name": message.name} if message.name else {}),
                    **({"tool_call_id": message.tool_call_id} if message.tool_call_id else {}),
                }
                for message in request.messages
            ],
        }
        temperature = (
            request.temperature if request.temperature is not None else self._settings.temperature
        )
        max_tokens = (
            request.max_tokens if request.max_tokens is not None else self._settings.max_tokens
        )
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if request.response_format is not None:
            payload["response_format"] = request.response_format
        return payload
