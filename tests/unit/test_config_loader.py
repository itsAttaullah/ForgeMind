"""Config loading precedence and validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from forgemind.config import (
    AgentProfile,
    ForgeMindConfig,
    load_config,
    profile_config,
)
from forgemind.core.enums import Permission
from forgemind.core.errors import ConfigurationError


def test_profile_defaults_readonly() -> None:
    cfg = profile_config(AgentProfile.READONLY)
    assert cfg.profile == AgentProfile.READONLY
    assert Permission.REPO_READ in cfg.policy.permissions
    assert Permission.REPO_WRITE not in cfg.policy.permissions
    assert cfg.budgets.max_repair_iterations == 0


def test_load_config_file_overrides_defaults(tmp_path: Path) -> None:
    path = tmp_path / "custom.toml"
    path.write_text(
        "\n".join(
            [
                'profile = "standard"',
                "[budgets]",
                "max_steps = 7",
                "[policy]",
                'permissions = ["repo.read"]',
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_config(config_file=path, environ={})
    assert cfg.budgets.max_steps == 7
    assert cfg.policy.permissions == [Permission.REPO_READ]


def test_env_overrides_file(tmp_path: Path) -> None:
    path = tmp_path / "base.toml"
    path.write_text(
        'profile = "standard"\n[budgets]\nmax_steps = 10\n',
        encoding="utf-8",
    )
    cfg = load_config(
        config_file=path,
        environ={"FORGEMIND_MAX_STEPS": "99", "FORGEMIND_LOG_LEVEL": "debug"},
    )
    assert cfg.budgets.max_steps == 99
    assert cfg.log_level == "DEBUG"


def test_cli_overrides_win(tmp_path: Path) -> None:
    path = tmp_path / "base.toml"
    path.write_text("[budgets]\nmax_steps = 10\n", encoding="utf-8")
    cfg = load_config(
        config_file=path,
        environ={"FORGEMIND_MAX_STEPS": "20"},
        overrides={"budgets": {"max_steps": 3}},
    )
    assert cfg.budgets.max_steps == 3


def test_explicit_profile_argument_preserved(tmp_path: Path) -> None:
    path = tmp_path / "file.toml"
    path.write_text('profile = "strict"\n[budgets]\nmax_steps = 12\n', encoding="utf-8")
    cfg = load_config(profile="readonly", config_file=path, environ={})
    assert cfg.profile == AgentProfile.READONLY
    assert cfg.budgets.max_steps == 12


def test_json_config_supported(tmp_path: Path) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(
        '{"profile":"standard","budgets":{"max_steps":11}}',
        encoding="utf-8",
    )
    cfg = load_config(config_file=path, environ={})
    assert cfg.budgets.max_steps == 11


def test_missing_config_file_raises() -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(config_file="definitely-missing-forgemind.toml", environ={})


def test_invalid_config_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("[budgets]\nmax_steps = 0\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(config_file=path, environ={})


def test_example_configs_load() -> None:
    root = Path(__file__).resolve().parents[2]
    for name in ("readonly.toml", "standard.toml", "strict.toml"):
        cfg = load_config(config_file=root / "configs" / name, environ={})
        assert isinstance(cfg, ForgeMindConfig)
        assert cfg.profile.value in {"readonly", "standard", "strict"}
