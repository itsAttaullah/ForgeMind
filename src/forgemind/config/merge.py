"""Deep-merge helpers and mapping utilities for config loading."""

from __future__ import annotations

from typing import Any


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overlay`` onto ``base`` without mutating inputs.

    Nested dicts are merged; all other values are replaced by ``overlay``.
    """

    result: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def drop_none(data: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose values are ``None`` (nested)."""

    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            nested = drop_none(value)
            if nested:
                cleaned[key] = nested
            continue
        cleaned[key] = value
    return cleaned
