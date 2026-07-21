"""OpenAI-compatible provider normalization and adapter tests."""

from __future__ import annotations

import asyncio
import json

import pytest

from forgemind.config.models import ProviderKind, ProviderSettings
from forgemind.core.enums import MessageRole
from forgemind.core.errors import ConfigurationError, ProviderError
from forgemind.core.messages import ChatMessage
from forgemind.core.provider import ProviderRequest
from forgemind.providers.http import HttpResponse
from forgemind.providers.normalize import normalize_openai_chat_completion
from forgemind.providers.openai_compat import OpenAICompatibleProvider


def test_normalize_openai_chat_completion() -> None:
    payload = {
        "id": "cmpl-1",
        "model": "gpt-test",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "hello"},
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
    }
    response = normalize_openai_chat_completion(payload)
    assert response.message.role == MessageRole.ASSISTANT
    assert response.message.content == "hello"
    assert response.model == "gpt-test"
    assert response.usage["total_tokens"] == 4


def test_openai_provider_success_with_mock_transport() -> None:
    body = {
        "model": "gpt-test",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "done"},
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }

    def transport(
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> HttpResponse:
        assert url == "https://example.test/v1/chat/completions"
        assert headers["Authorization"] == "Bearer test-key"
        return HttpResponse(
            status_code=200,
            body=json.dumps(body).encode("utf-8"),
            headers={},
        )

    settings = ProviderSettings(
        kind=ProviderKind.OPENAI_COMPATIBLE,
        model="gpt-test",
        base_url="https://example.test/v1",
    )
    provider = OpenAICompatibleProvider(
        settings=settings,
        api_key="test-key",
        transport=transport,
    )
    request = ProviderRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="hi")],
    )
    response = asyncio.run(provider.complete(request))
    assert response.message.content == "done"


def test_openai_provider_maps_http_error() -> None:
    def transport(
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> HttpResponse:
        return HttpResponse(
            status_code=401,
            body=json.dumps({"error": {"message": "invalid api key"}}).encode("utf-8"),
            headers={},
        )

    provider = OpenAICompatibleProvider(
        settings=ProviderSettings(kind=ProviderKind.OPENAI_COMPATIBLE, model="gpt-test"),
        api_key="bad",
        transport=transport,
    )
    request = ProviderRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="hi")],
    )
    with pytest.raises(ProviderError, match="401") as exc_info:
        asyncio.run(provider.complete(request))
    assert exc_info.value.status_code == 401


def test_openai_provider_requires_model() -> None:
    provider = OpenAICompatibleProvider(
        settings=ProviderSettings(kind=ProviderKind.OPENAI_COMPATIBLE),
        api_key="key",
        transport=lambda url, **kwargs: HttpResponse(status_code=200, body=b"{}", headers={}),
    )
    request = ProviderRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="hi")],
    )
    with pytest.raises(ConfigurationError, match="model is required"):
        asyncio.run(provider.complete(request))
