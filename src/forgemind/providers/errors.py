"""Provider error mapping helpers."""

from __future__ import annotations

import json

from forgemind.core.errors import ProviderError
from forgemind.providers.http import HttpResponse


def raise_for_http_response(response: HttpResponse, *, provider: str) -> None:
    """Raise ``ProviderError`` when ``response`` indicates failure."""

    if 200 <= response.status_code < 300:
        return

    body_text = response.body.decode("utf-8", errors="replace")
    detail = _extract_error_message(body_text)
    message = f"{provider} request failed ({response.status_code})"
    if detail:
        message = f"{message}: {detail}"
    raise ProviderError(message, status_code=response.status_code, body=body_text)


def map_transport_error(exc: Exception, *, provider: str) -> ProviderError:
    """Wrap low-level transport failures as ``ProviderError``."""

    return ProviderError(f"{provider} transport error: {exc}")


def _extract_error_message(body_text: str) -> str | None:
    if not body_text.strip():
        return None
    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        return body_text.strip()[:500]
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return body_text.strip()[:500]
