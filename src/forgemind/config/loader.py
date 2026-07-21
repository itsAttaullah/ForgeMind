"""Layered configuration loader: defaults → file → env → overrides."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from forgemind.config.defaults import profile_config
from forgemind.config.env import env_overrides
from forgemind.config.merge import deep_merge, drop_none
from forgemind.config.models import AgentProfile, ForgeMindConfig
from forgemind.core.errors import ConfigurationError


def load_config(
    *,
    profile: AgentProfile | str | None = None,
    config_file: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> ForgeMindConfig:
    """Load config with precedence: defaults → file → env → CLI overrides.

    Args:
        profile: Built-in profile used as the defaults base. If omitted, uses
            ``standard``, unless the file/env/overrides set ``profile``.
        config_file: Optional TOML or JSON file.
        environ: Environment mapping (defaults to ``os.environ`` when applying env).
        overrides: Highest-precedence partial config mapping (CLI / programmatic).
    """

    try:
        base_profile = AgentProfile(profile) if profile is not None else AgentProfile.STANDARD
        data: dict[str, Any] = profile_config(base_profile).model_dump(mode="json")

        if config_file is not None:
            file_data = _load_config_file(Path(config_file))
            data = deep_merge(data, file_data)
            # If the file selects a different profile and no explicit profile was
            # requested, re-base defaults on that profile then re-apply the file.
            if profile is None and "profile" in file_data:
                file_profile = AgentProfile(str(file_data["profile"]))
                data = profile_config(file_profile).model_dump(mode="json")
                data = deep_merge(data, file_data)

        data = deep_merge(data, env_overrides(environ))

        if overrides:
            data = deep_merge(data, drop_none(dict(overrides)))

        if profile is not None:
            data["profile"] = str(base_profile)

        return ForgeMindConfig.model_validate(data)
    except (OSError, ValueError, PydanticValidationError, KeyError, TypeError) as exc:
        raise ConfigurationError(f"failed to load config: {exc}") from exc


def _load_config_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigurationError(f"config file not found: {path}")

    suffix = path.suffix.lower()
    raw = path.read_bytes()
    if suffix == ".toml":
        loaded = tomllib.loads(raw.decode("utf-8"))
    elif suffix == ".json":
        loaded = json.loads(raw.decode("utf-8"))
    else:
        raise ConfigurationError(
            f"unsupported config format '{suffix}' (use .toml or .json): {path}"
        )

    if not isinstance(loaded, dict):
        raise ConfigurationError(f"config root must be a table/object: {path}")
    return loaded
