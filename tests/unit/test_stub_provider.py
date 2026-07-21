"""Stub provider tests."""

from __future__ import annotations

import asyncio

from forgemind.core.enums import MessageRole
from forgemind.core.messages import ChatMessage
from forgemind.core.provider import ProviderRequest
from forgemind.providers import StubProvider


def test_stub_echoes_last_user_message() -> None:
    provider = StubProvider()
    request = ProviderRequest(
        messages=[
            ChatMessage(role=MessageRole.SYSTEM, content="You are helpful."),
            ChatMessage(role=MessageRole.USER, content="Explain JWT"),
        ]
    )
    response = asyncio.run(provider.complete(request))
    assert response.message.content == "stub: Explain JWT"
    assert response.finish_reason == "stop"


def test_stub_uses_queued_responses() -> None:
    provider = StubProvider(responses=["first", "second"])
    request = ProviderRequest(messages=[ChatMessage(role=MessageRole.USER, content="x")])
    first = asyncio.run(provider.complete(request))
    second = asyncio.run(provider.complete(request))
    assert first.message.content == "first"
    assert second.message.content == "second"


def test_stub_metadata_override() -> None:
    provider = StubProvider(responses=["ignored"])
    request = ProviderRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="x")],
        metadata={"stub_response": "custom"},
    )
    response = asyncio.run(provider.complete(request))
    assert response.message.content == "custom"
