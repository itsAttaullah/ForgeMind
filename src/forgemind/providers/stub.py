"""Deterministic stub provider for tests and offline development."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

from forgemind.core.enums import MessageRole
from forgemind.core.messages import ChatMessage
from forgemind.core.provider import ProviderRequest, ProviderResponse


class StubProvider:
    """Return scripted or derived responses without network I/O."""

    def __init__(
        self,
        *,
        default_model: str = "stub-model",
        responses: list[str] | None = None,
        responder: Callable[[ProviderRequest], str] | None = None,
    ) -> None:
        self._default_model = default_model
        self._queue: deque[str] = deque(responses or [])
        self._responder = responder

    def queue(self, *responses: str) -> None:
        """Append fixed responses consumed in FIFO order."""

        self._queue.extend(responses)

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        content = self._next_content(request)
        return ProviderResponse(
            message=ChatMessage(role=MessageRole.ASSISTANT, content=content),
            model=request.model or self._default_model,
            finish_reason="stop",
            usage={"prompt_tokens": 0, "completion_tokens": len(content.split())},
            raw={"stub": True},
        )

    def _next_content(self, request: ProviderRequest) -> str:
        metadata = request.metadata
        override = metadata.get("stub_response")
        if isinstance(override, str):
            return override

        if self._queue:
            return self._queue.popleft()

        if self._responder is not None:
            return self._responder(request)

        last_user = next(
            (
                message.content
                for message in reversed(request.messages)
                if message.role == MessageRole.USER
            ),
            "",
        )
        if last_user:
            return f"stub: {last_user}"
        return "stub: ready"
