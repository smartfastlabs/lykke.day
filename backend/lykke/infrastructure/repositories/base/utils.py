"""Utility functions for repository operations."""

from collections.abc import Iterable
from dataclasses import fields, is_dataclass
from datetime import datetime, time as dt_time
from enum import Enum
from typing import Any, TypeVar, get_origin, get_type_hints
from uuid import UUID

import pydantic

from lykke.core.utils.dates import ensure_utc

E = TypeVar("E", bound=Enum)


def filter_init_false_fields(
    data: dict[str, Any], entity_class: type[Any]
) -> dict[str, Any]:
    """Filter out fields with init=False from a dictionary.

    When deserializing from the database, fields with init=False (like _domain_events)
    should not be passed to the entity constructor.

    Args:
        data: Dictionary containing data to filter
        entity_class: The entity class to check for init=False fields

    Returns:
        Filtered dictionary with init=False fields removed
    """
    if not is_dataclass(entity_class):
        return data

    init_false_fields = {f.name for f in fields(entity_class) if not f.init}
    return {k: v for k, v in data.items() if k not in init_false_fields}


def normalize_list_fields(data: dict[str, Any], model: type[Any]) -> dict[str, Any]:
    """Normalize None values to empty lists for list-typed fields.

    This function inspects a dataclass or Pydantic model's field annotations and converts
    None values to [] for fields that are typed as lists. This is necessary
    because databases may return None for JSONB array fields, but models
    expect list types (even with default_factory) to receive list values.

    Args:
        data: Dictionary containing row data from the database
        model: Dataclass or Pydantic model class to inspect for list-typed fields

    Returns:
        Dictionary with None values converted to [] for list-typed fields
    """
    normalized = data.copy()

    # Handle dataclasses
    if is_dataclass(model):
        type_hints = get_type_hints(model)
        for field in fields(model):
            # Skip if field not in data
            if field.name not in normalized:
                continue

            # Skip if value is not None
            if normalized[field.name] is not None:
                continue

            # Get the field annotation
            annotation = type_hints.get(field.name, field.type)

            # Check if the annotation is a list type
            origin = get_origin(annotation)
            if origin is list:
                # This is a list type, normalize None to []
                normalized[field.name] = []
        return normalized

    # Handle Pydantic models
    if isinstance(model, type) and issubclass(model, pydantic.BaseModel):
        # Get the model's field annotations
        for field_name, field_info in model.model_fields.items():
            # Skip if field not in data
            if field_name not in normalized:
                continue

            # Skip if value is not None
            if normalized[field_name] is not None:
                continue

            # Get the field annotation
            annotation = field_info.annotation

            # Check if the annotation is a list type
            origin = get_origin(annotation)
            if origin is list:
                # This is a list type, normalize None to []
                normalized[field_name] = []

    return normalized


def ensure_datetime_utc(value: datetime | None) -> datetime | None:
    """Normalize a datetime to UTC with tzinfo set."""
    return ensure_utc(value)


def ensure_datetimes_utc(
    data: dict[str, Any],
    keys: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Set tzinfo=UTC on datetimes, optionally limiting to specific keys."""
    normalized = dict(data)
    if keys is None:
        keys = normalized.keys()

    for key in keys:
        value = normalized.get(key)
        if isinstance(value, datetime):
            normalized[key] = ensure_datetime_utc(value)
    return normalized


def enum_to_value(value: Enum | str | None) -> str | None:
    """Safely convert an enum to its string value.

    Handles both enum instances and already-converted strings.

    Args:
        value: Enum instance, string, or None

    Returns:
        The enum's value as a string, or None
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value.value)


def str_to_enum(value: str | E | None, enum_class: type[E]) -> E | None:
    """Convert a string to an enum, or return as-is if already an enum.

    Args:
        value: String value, enum instance, or None
        enum_class: The enum class to convert to

    Returns:
        The enum instance, or None
    """
    if value is None:
        return None
    if isinstance(value, enum_class):
        return value
    return enum_class(value)


def str_to_time(value: str | dt_time | None) -> dt_time | None:
    """Convert a time string to a time object.

    Args:
        value: ISO format time string, time object, or None

    Returns:
        The time object, or None
    """
    if value is None:
        return None
    if isinstance(value, dt_time):
        return value
    return dt_time.fromisoformat(value)


def str_to_uuid(value: str | UUID | None) -> UUID | None:
    """Convert a string to a UUID.

    Args:
        value: UUID string, UUID object, or None

    Returns:
        The UUID object, or None
    """
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(value)


def convert_enum_fields(
    data: dict[str, Any],
    field_enum_map: dict[str, type[Enum]],
) -> dict[str, Any]:
    """Convert multiple string fields to their enum types.

    Args:
        data: Dictionary containing data to convert
        field_enum_map: Mapping of field names to enum classes

    Returns:
        Dictionary with enum fields converted

    Example:
        >>> data = {"status": "active", "type": "task"}
        >>> convert_enum_fields(data, {"status": TaskStatus, "type": TaskType})
        {"status": TaskStatus.ACTIVE, "type": TaskType.TASK}
    """
    result = dict(data)
    for field_name, enum_class in field_enum_map.items():
        if field_name in result:
            result[field_name] = str_to_enum(result[field_name], enum_class)
    return result


def convert_time_fields(
    data: dict[str, Any],
    field_names: Iterable[str],
) -> dict[str, Any]:
    """Convert multiple time string fields to time objects.

    Args:
        data: Dictionary containing data to convert
        field_names: Names of fields to convert

    Returns:
        Dictionary with time fields converted
    """
    result = dict(data)
    for field_name in field_names:
        if field_name in result:
            result[field_name] = str_to_time(result[field_name])
    return result
