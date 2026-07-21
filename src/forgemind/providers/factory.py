"""Provider factory helpers."""

from __future__ import annotations

import os
from collections.abc import Mapping

from forgemind.config.models import ForgeMindConfig, ProviderKind, ProviderSettings
from forgemind.core.errors import ConfigurationError
from forgemind.providers.openai_compat import OpenAICompatibleProvider
from forgemind.providers.stub import StubProvider


def create_provider(
    config: ForgeMindConfig,
    *,
    environ: Mapping[str, str] | None = None,
    api_key: str | None = None,
) -> StubProvider | OpenAICompatibleProvider:
    """Instantiate the configured provider adapter."""

    return create_provider_from_settings(
        config.provider,
        environ=environ,
        api_key=api_key,
    )


def create_provider_from_settings(
    settings: ProviderSettings,
    *,
    environ: Mapping[str, str] | None = None,
    api_key: str | None = None,
) -> StubProvider | OpenAICompatibleProvider:
    """Instantiate a provider from ``ProviderSettings``."""

    if settings.kind == ProviderKind.STUB:
        return StubProvider(default_model=settings.model or "stub-model")

    if settings.kind == ProviderKind.OPENAI_COMPATIBLE:
        resolved_key = api_key or _read_api_key(settings, environ)
        return OpenAICompatibleProvider(settings=settings, api_key=resolved_key)

    raise ConfigurationError(f"unsupported provider kind: {settings.kind}")


def _read_api_key(
    settings: ProviderSettings,
    environ: Mapping[str, str] | None,
) -> str | None:
    if environ is None:
        return None
    value = environ.get(settings.api_key_env)
    if value and value.strip():
        return value.strip()
    return None


def resolve_api_key(settings: ProviderSettings) -> str | None:
    """Read the configured API key from ``os.environ`` if present."""

    value = os.environ.get(settings.api_key_env)
    if value and value.strip():
        return value.strip()
    return None
