"""JSON Schema validation for zLoop state and results."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from jsonschema import validate, ValidationError

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

_schemas: Dict[str, Any] = {}


def _load_schema(name: str) -> Dict[str, Any]:
    if name not in _schemas:
        path = os.path.join(SCHEMA_DIR, f"{name}.schema.json")
        with open(path, "r", encoding="utf-8") as f:
            _schemas[name] = json.load(f)
    return _schemas[name]


def validate_loop_state(data: Dict[str, Any]) -> None:
    """Validate loop state dict against loop-state.schema.json.
    
    Raises:
        jsonschema.ValidationError: if data does not conform to schema.
    """
    schema = _load_schema("loop-state")
    validate(instance=data, schema=schema)


def validate_agent_result(data: Dict[str, Any]) -> None:
    """Validate agent result dict against agent-result.schema.json.
    
    Raises:
        jsonschema.ValidationError: if data does not conform to schema.
    """
    schema = _load_schema("agent-result")
    validate(instance=data, schema=schema)


def validate_verification_result(data: Dict[str, Any]) -> None:
    """Validate verification result dict against verification-result.schema.json.
    
    Raises:
        jsonschema.ValidationError: if data does not conform to schema.
    """
    schema = _load_schema("verification-result")
    validate(instance=data, schema=schema)


def is_valid_loop_state(data: Dict[str, Any]) -> bool:
    """Return True if data conforms to loop-state schema."""
    try:
        validate_loop_state(data)
        return True
    except ValidationError:
        return False


def is_valid_agent_result(data: Dict[str, Any]) -> bool:
    """Return True if data conforms to agent-result schema."""
    try:
        validate_agent_result(data)
        return True
    except ValidationError:
        return False
