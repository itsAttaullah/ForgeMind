"""Argument validation against tool parameter schemas."""

from __future__ import annotations

from typing import Any

from forgemind.core.errors import ValidationError
from forgemind.core.tools import ToolParameterSchema


def validate_tool_arguments(
    schema: ToolParameterSchema,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Validate ``arguments`` against a tool parameter schema.

    Raises:
        ValidationError: When required keys are missing, unknown keys appear,
            or declared property types do not match.
    """

    if not isinstance(arguments, dict):
        raise ValidationError("tool arguments must be an object")

    missing = [key for key in schema.required if key not in arguments]
    if missing:
        raise ValidationError(f"missing required arguments: {', '.join(missing)}")

    if not schema.additional_properties:
        unknown = [key for key in arguments if key not in schema.properties]
        if unknown:
            raise ValidationError(f"unexpected arguments: {', '.join(sorted(unknown))}")

    for key, value in arguments.items():
        prop = schema.properties.get(key)
        if not isinstance(prop, dict):
            continue
        expected = prop.get("type")
        if expected is None:
            continue
        if not _matches_json_type(value, str(expected)):
            raise ValidationError(
                f"argument '{key}' expected type {expected}, got {type(value).__name__}"
            )

    return dict(arguments)


def _matches_json_type(value: Any, expected: str) -> bool:
    mapping: dict[str, type | tuple[type, ...]] = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
        "null": type(None),
    }
    # JSON Schema often allows integer for number; reject bool as int.
    if expected == "integer" and isinstance(value, bool):
        return False
    if expected == "number" and isinstance(value, bool):
        return False
    py_type = mapping.get(expected)
    if py_type is None:
        return True
    return isinstance(value, py_type)
