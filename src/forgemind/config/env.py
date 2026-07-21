"""Environment variable overlays for ForgeMind config."""

from __future__ import annotations

import os
from collections.abc import Mapping

from forgemind.config.merge import drop_none


def env_overrides(environ: Mapping[str, str] | None = None) -> dict[str, object]:
    """Build a partial config dict from ``FORGEMIND_*`` environment variables."""

    env = environ if environ is not None else os.environ
    overlay: dict[str, object] = drop_none(
        {
            "profile": env.get("FORGEMIND_PROFILE"),
            "log_level": env.get("FORGEMIND_LOG_LEVEL"),
            "budgets": drop_none(
                {
                    "max_steps": _int(env, "FORGEMIND_MAX_STEPS"),
                    "max_tool_calls": _int(env, "FORGEMIND_MAX_TOOL_CALLS"),
                    "max_repair_iterations": _int(env, "FORGEMIND_MAX_REPAIR_ITERATIONS"),
                    "timeout_seconds": _float(env, "FORGEMIND_TIMEOUT_SECONDS"),
                    "max_cost_usd": _float(env, "FORGEMIND_MAX_COST_USD"),
                }
            ),
            "provider": drop_none(
                {
                    "model": env.get("FORGEMIND_MODEL"),
                    "temperature": _float(env, "FORGEMIND_TEMPERATURE"),
                    "max_tokens": _int(env, "FORGEMIND_MAX_TOKENS"),
                    "base_url": env.get("FORGEMIND_BASE_URL"),
                }
            ),
            "policy": drop_none(
                {
                    "permissions": _csv(env, "FORGEMIND_PERMISSIONS"),
                }
            ),
        }
    )
    return overlay


def _int(env: Mapping[str, str], key: str) -> int | None:
    raw = env.get(key)
    if raw is None or raw.strip() == "":
        return None
    return int(raw)


def _float(env: Mapping[str, str], key: str) -> float | None:
    raw = env.get(key)
    if raw is None or raw.strip() == "":
        return None
    return float(raw)


def _csv(env: Mapping[str, str], key: str) -> list[str] | None:
    raw = env.get(key)
    if raw is None or raw.strip() == "":
        return None
    return [part.strip() for part in raw.split(",") if part.strip()]
