"""JSON Schema validation for zLoop state and results."""

from __future__ import annotations

import json
import os
from typing import Any

from jsonschema import ValidationError, validate

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

_schemas: dict[str, Any] = {}


def _load_schema(name: str) -> dict[str, Any]:
    if name not in _schemas:
        path = os.path.join(SCHEMA_DIR, f"{name}.schema.json")
        with open(path, encoding="utf-8") as f:
            loaded: dict[str, Any] = json.load(f)
            _schemas[name] = loaded
    return _schemas[name]  # type: ignore[no-any-return]


def validate_loop_state(data: dict[str, Any]) -> None:
    """Validate loop state dict against loop-state.schema.json.

    Raises:
        ValidationError: if data does not conform to schema.
    """
    schema = _load_schema("loop-state")
    validate(instance=data, schema=schema)


def validate_agent_result(data: dict[str, Any]) -> None:
    """Validate agent result dict against agent-result.schema.json.

    Raises:
        ValidationError: if data does not conform to schema.
    """
    schema = _load_schema("agent-result")
    validate(instance=data, schema=schema)


def validate_verification_result(data: dict[str, Any]) -> None:
    """Verify verification result dict against verification-result.schema.json.

    Raises:
        ValidationError: if data does not conform to schema.
    """
    schema = _load_schema("verification-result")
    validate(instance=data, schema=schema)


def is_valid_loop_state(data: dict[str, Any]) -> bool:
    """Return True if data conforms to loop-state schema."""
    try:
        validate_loop_state(data)
        return True
    except ValidationError:
        return False


def is_valid_agent_result(data: dict[str, Any]) -> bool:
    """Return True if data conforms to agent-result schema."""
    try:
        validate_agent_result(data)
        return True
    except ValidationError:
        return False
