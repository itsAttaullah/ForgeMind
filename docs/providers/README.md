# Model providers (Phase 3)

ForgeMind talks to LLMs through the ``ModelProvider`` port (`forgemind.core.protocols.ModelProvider`).
Phase 3 ships two built-in adapters:

| Kind | Class | Use |
|------|-------|-----|
| `stub` | `StubProvider` | Tests and offline development (default) |
| `openai_compatible` | `OpenAICompatibleProvider` | OpenAI API and compatible gateways |

---

## Quick start

```python
import asyncio

from forgemind.config import load_config
from forgemind.core.enums import MessageRole
from forgemind.core.messages import ChatMessage
from forgemind.core.provider import ProviderRequest
from forgemind.providers import create_provider

config = load_config(profile="standard")
provider = create_provider(config)

request = ProviderRequest(
    messages=[ChatMessage(role=MessageRole.USER, content="Summarize this repo")],
)

response = asyncio.run(provider.complete(request))
print(response.message.content)
```

Default config uses the **stub** provider (no network, no API key).

---

## OpenAI-compatible provider

Set provider kind and credentials:

```bash
# .env (never commit)
FORGEMIND_PROVIDER=openai_compatible
FORGEMIND_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
# optional override for local gateways (Ollama, vLLM, etc.)
# FORGEMIND_BASE_URL=http://127.0.0.1:11434/v1
```

Or in TOML:

```toml
[provider]
kind = "openai_compatible"
model = "gpt-4o-mini"
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
timeout_seconds = 60.0
```

```python
provider = create_provider(config)  # reads OPENAI_API_KEY from environment
response = asyncio.run(provider.complete(request))
```

### Normalized response

All adapters return ``ProviderResponse``:

- ``message`` — assistant ``ChatMessage``
- ``model`` — resolved model id
- ``finish_reason`` — vendor stop reason when available
- ``usage`` — token counts when available
- ``raw`` — vendor payload (for debugging)

HTTP and transport failures raise ``ProviderError`` with optional ``status_code`` and ``body``.

---

## Stub provider

Deterministic, no network:

```python
from forgemind.providers import StubProvider

provider = StubProvider(responses=["plan step 1", "plan step 2"])
```

Per-request override:

```python
ProviderRequest(
    messages=[...],
    metadata={"stub_response": "fixed output"},
)
```

If no queue/metadata/responder is set, the stub echoes the last user message as ``stub: <text>``.

---

## Configuration reference

| Setting | Env var | Default |
|---------|---------|---------|
| `provider.kind` | `FORGEMIND_PROVIDER` | `stub` |
| `provider.model` | `FORGEMIND_MODEL` | `None` |
| `provider.base_url` | `FORGEMIND_BASE_URL` | OpenAI v1 URL |
| `provider.api_key_env` | `FORGEMIND_API_KEY_ENV` | `OPENAI_API_KEY` |
| `provider.timeout_seconds` | `FORGEMIND_PROVIDER_TIMEOUT_SECONDS` | `60` |
| `provider.temperature` | `FORGEMIND_TEMPERATURE` | `None` |
| `provider.max_tokens` | `FORGEMIND_MAX_TOKENS` | `None` |

Precedence follows the global config loader: **profile defaults → file → env → overrides**.

---

## Adding a new provider

1. Implement ``async def complete(self, request: ProviderRequest) -> ProviderResponse``.
2. Map vendor errors to ``ProviderError`` (include status/body when useful).
3. Return normalized ``ProviderResponse`` — do not leak vendor-specific types to callers.
4. Register the adapter in ``forgemind.providers.factory.create_provider_from_settings``.
5. Add ``ProviderKind`` value + docs + unit tests with mocked transport.

Keep HTTP/SDK details inside the adapter module; the orchestrator (Phase 6+) depends only on the port.

---

## Testing guidance

- Unit tests must **not** call live APIs.
- Inject a fake ``transport`` into ``OpenAICompatibleProvider`` (see ``tests/unit/test_openai_provider.py``).
- Use ``StubProvider`` for orchestrator tests in later phases.
