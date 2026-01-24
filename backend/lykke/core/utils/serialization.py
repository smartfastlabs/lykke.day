"""Utilities for serializing dataclasses to JSON-compatible formats."""

from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import Any
from uuid import UUID


def dataclass_to_json_dict(obj: Any) -> dict[str, Any] | Any:
    """Convert a dataclass instance to a JSON-compatible dictionary.

    Handles:
    - Nested dataclasses
    - Enums (converted to their values)
    - UUIDs (converted to strings)
    - Dates, datetimes, and times (converted to ISO strings)
    - Lists and dicts (recursively processed)
    - None values (preserved)

    Args:
        obj: The dataclass instance to serialize.

    Returns:
        A JSON-compatible dictionary, or the original object if not serializable.
    """
    if obj is None:
        return None

    if is_dataclass(obj):
        result_dict: dict[str, Any] = {}
        for field in fields(obj):
            value = getattr(obj, field.name)
            result_dict[field.name] = _serialize_value(value)
        return result_dict

    # If it's not a dataclass, try asdict as fallback
    if hasattr(obj, "__dict__"):
        result_dict2: dict[str, Any] = {}
        for key, value in obj.__dict__.items():
            result_dict2[key] = _serialize_value(value)
        return result_dict2

    return obj


def _serialize_value(value: Any) -> Any:
    """Serialize a single value to JSON-compatible format."""
    if value is None:
        return None

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, list):
        return [_serialize_value(item) for item in value]

    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}

    if is_dataclass(value):
        return dataclass_to_json_dict(value)

    return value
