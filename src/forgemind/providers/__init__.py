"""Model provider adapters (Phase 3)."""

from __future__ import annotations

from forgemind.providers.factory import (
    create_provider,
    create_provider_from_settings,
    resolve_api_key,
)
from forgemind.providers.openai_compat import DEFAULT_OPENAI_BASE_URL, OpenAICompatibleProvider
from forgemind.providers.stub import StubProvider

__all__ = [
    "DEFAULT_OPENAI_BASE_URL",
    "OpenAICompatibleProvider",
    "StubProvider",
    "create_provider",
    "create_provider_from_settings",
    "resolve_api_key",
]
