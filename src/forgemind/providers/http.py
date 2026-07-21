"""HTTP transport helpers for provider adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """Minimal HTTP response envelope."""

    status_code: int
    body: bytes
    headers: dict[str, str]


def post_json(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> HttpResponse:
    """POST JSON to ``url`` using stdlib urllib (sync)."""

    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_headers = {key.lower(): value for key, value in response.headers.items()}
            return HttpResponse(
                status_code=response.status,
                body=response.read(),
                headers=raw_headers,
            )
    except HTTPError as exc:
        return HttpResponse(
            status_code=exc.code,
            body=exc.read(),
            headers={key.lower(): value for key, value in exc.headers.items()},
        )
    except URLError as exc:
        raise exc
