"""Argument validation tests."""

from __future__ import annotations

import pytest

from forgemind.core.errors import ValidationError
from forgemind.core.tools import ToolParameterSchema
from forgemind.tools import validate_tool_arguments


def test_validate_required_and_types() -> None:
    schema = ToolParameterSchema(
        properties={"path": {"type": "string"}, "limit": {"type": "integer"}},
        required=["path"],
    )
    args = validate_tool_arguments(schema, {"path": "a.py", "limit": 3})
    assert args["path"] == "a.py"


def test_validate_missing_required() -> None:
    schema = ToolParameterSchema(properties={"path": {"type": "string"}}, required=["path"])
    with pytest.raises(ValidationError, match="missing required"):
        validate_tool_arguments(schema, {})


def test_validate_unexpected_keys() -> None:
    schema = ToolParameterSchema(properties={"path": {"type": "string"}}, required=["path"])
    with pytest.raises(ValidationError, match="unexpected"):
        validate_tool_arguments(schema, {"path": "a.py", "extra": 1})


def test_validate_wrong_type() -> None:
    schema = ToolParameterSchema(properties={"limit": {"type": "integer"}}, required=["limit"])
    with pytest.raises(ValidationError, match="expected type integer"):
        validate_tool_arguments(schema, {"limit": "nope"})
