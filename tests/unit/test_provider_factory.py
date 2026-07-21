"""Provider factory tests."""

from __future__ import annotations

from forgemind.config import (
    AgentProfile,
    ForgeMindConfig,
    ProviderKind,
    load_config,
    profile_config,
)
from forgemind.providers import OpenAICompatibleProvider, StubProvider, create_provider


def test_factory_creates_stub_by_default() -> None:
    config = profile_config(AgentProfile.STANDARD)
    provider = create_provider(config)
    assert isinstance(provider, StubProvider)


def test_factory_creates_openai_compatible() -> None:
    config = ForgeMindConfig(
        provider=profile_config(AgentProfile.STANDARD).provider.model_copy(
            update={"kind": ProviderKind.OPENAI_COMPATIBLE, "model": "gpt-test"}
        )
    )
    provider = create_provider(config, api_key="secret")
    assert isinstance(provider, OpenAICompatibleProvider)


def test_load_config_provider_kind_from_env() -> None:
    cfg = load_config(
        profile=AgentProfile.STANDARD,
        environ={"FORGEMIND_PROVIDER": "openai_compatible", "FORGEMIND_MODEL": "gpt-test"},
    )
    assert cfg.provider.kind == ProviderKind.OPENAI_COMPATIBLE
    assert cfg.provider.model == "gpt-test"
