"""Utilities for serializing and deserializing DomainEvent instances for pub/sub messaging.

DomainEvents are Python dataclass instances that need to be serialized to JSON
for Redis pub/sub broadcasting, then deserialized back to the original event type
on the receiving end (WebSocket handlers).
"""

import importlib
from dataclasses import asdict, fields, is_dataclass
from datetime import date as dt_date, datetime, time
from enum import Enum
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints
from uuid import UUID

from lykke.domain.events.base import DomainEvent

_DEFAULT_TYPE_HINTS: dict[str, Any] = {
    "UUID": UUID,
    "datetime": datetime,
    "date": dt_date,
    "dt_date": dt_date,
    "time": time,
    "Any": Any,
}


def serialize_domain_event(event: DomainEvent) -> dict[str, Any]:
    """Serialize a DomainEvent instance to a JSON-compatible dictionary for pub/sub.

    The serialized format includes:
    - event_type: Fully qualified class name (module.ClassName)
    - event_data: All event fields as JSON-serializable values
    - occurred_at: ISO format timestamp

    Args:
        event: The DomainEvent instance to serialize

    Returns:
        A JSON-compatible dictionary with event type and data

    Example:
        >>> event = TaskCompletedEvent(
        ...     user_id=uuid4(),
        ...     task_id=uuid4(),
        ...     completed_at=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        ... )
        >>> serialize_domain_event(event)
        {
            "event_type": "lykke.domain.events.task_events.TaskCompletedEvent",
            "event_data": {
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "completed_at": "2024-01-01T12:00:00+00:00",
                "occurred_at": "2024-01-01T12:00:05.123456+00:00"
            }
        }
    """
    if not isinstance(event, DomainEvent):
        raise TypeError(f"Expected DomainEvent, got {type(event)}")

    if not is_dataclass(event):
        raise TypeError(f"Event {type(event)} must be a dataclass")

    event_type = f"{event.__class__.__module__}.{event.__class__.__name__}"

    event_dict = asdict(event)

    json_safe_data: dict[str, Any] = {}
    for key, value in event_dict.items():
        json_safe_data[key] = _serialize_value(value)

    return {
        "event_type": event_type,
        "event_data": json_safe_data,
    }


def _serialize_value(value: Any) -> Any:
    """Recursively serialize a value to JSON-compatible format.

    Handles:
    - datetime, date, time -> ISO format strings
    - UUID -> string
    - Enum -> value
    - dict -> recursively serialize values
    - list -> recursively serialize items
    - Other types -> pass through (primitives)
    """
    if isinstance(value, (datetime, dt_date, time)):
        return value.isoformat()
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, Enum):
        return value.value
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_value(item) for item in value]
    else:
        return value


def deserialize_domain_event(data: dict[str, Any]) -> DomainEvent:
    """Deserialize a dictionary back to a DomainEvent instance.

    Args:
        data: Dictionary with 'event_type' and 'event_data' keys

    Returns:
        A DomainEvent instance of the appropriate type

    Raises:
        ValueError: If event_type is invalid or module cannot be imported
        TypeError: If the deserialized class is not a DomainEvent

    Example:
        >>> data = {
        ...     "event_type": "lykke.domain.events.task_events.TaskCompletedEvent",
        ...     "event_data": {
        ...         "task_id": "123e4567-e89b-12d3-a456-426614174000",
        ...         "completed_at": "2024-01-01T12:00:00+00:00"
        ...     }
        ... }
        >>> event = deserialize_domain_event(data)
        >>> isinstance(event, TaskCompletedEvent)
        True
    """
    if "event_type" not in data or "event_data" not in data:
        raise ValueError("Invalid event data: missing 'event_type' or 'event_data'")

    event_type = data["event_type"]
    event_data = data["event_data"]

    try:
        module_name, class_name = event_type.rsplit(".", 1)
    except ValueError as e:
        raise ValueError(f"Invalid event_type format: {event_type}") from e

    try:
        module = importlib.import_module(module_name)
        event_class = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Could not load event class {event_type}: {e}") from e

    if not issubclass(event_class, DomainEvent):
        raise TypeError(f"Event class {event_type} is not a DomainEvent")

    try:
        coerced_event_data = _coerce_event_data(event_class, event_data)
        event = event_class(**coerced_event_data)
    except TypeError as e:
        raise ValueError(
            f"Could not instantiate {event_type} with provided data: {e}"
        ) from e

    from typing import cast

    return cast("DomainEvent", event)


class _SafeTypeNamespace(dict):
    def __missing__(self, key: str) -> Any:
        return object


def _build_type_hint_namespace(event_class: type[DomainEvent]) -> dict[str, Any]:
    module = importlib.import_module(event_class.__module__)
    namespace = _SafeTypeNamespace(vars(module))
    namespace.update(_DEFAULT_TYPE_HINTS)
    return namespace


def _get_event_type_hints(
    event_class: type[DomainEvent], namespace: dict[str, Any]
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for cls in reversed(event_class.mro()):
        if not issubclass(cls, DomainEvent):
            continue
        if cls is object:
            continue
        cls_namespace = namespace
        if cls is not event_class:
            cls_namespace = _build_type_hint_namespace(cls)
        try:
            hints = get_type_hints(
                cls, globalns=cls_namespace, localns=cls_namespace, include_extras=True
            )
        except (NameError, TypeError, SyntaxError):
            hints = {}
        merged.update(hints)
    return merged


def _coerce_event_data(
    event_class: type[DomainEvent], event_data: dict[str, Any]
) -> dict[str, Any]:
    """Coerce serialized event data into annotated field types."""
    coerced_data: dict[str, Any] = dict(event_data)
    namespace = _build_type_hint_namespace(event_class)
    type_hints = _get_event_type_hints(event_class, namespace)
    for field in fields(event_class):
        if field.name not in event_data:
            continue
        resolved_annotation = type_hints.get(field.name, field.type)
        coerced_data[field.name] = _coerce_value(
            event_data[field.name], resolved_annotation
        )
    return coerced_data


def _coerce_value(value: Any, annotation: Any) -> Any:
    """Coerce a JSON value to the annotated type when possible."""
    if value is None:
        return None

    origin = get_origin(annotation)
    if origin in (list, tuple):
        args = get_args(annotation)
        item_type = args[0] if args else Any
        if isinstance(value, list):
            return [_coerce_value(item, item_type) for item in value]
        return value
    if origin is dict:
        key_type, value_type = ((*get_args(annotation), Any, Any))[:2]
        if isinstance(value, dict):
            return {
                _coerce_value(key, key_type): _coerce_value(val, value_type)
                for key, val in value.items()
            }
        return value
    if origin in (UnionType, Union):
        for arg in get_args(annotation):
            if arg is type(None):
                continue
            coerced = _coerce_value(value, arg)
            if coerced is not value:
                return coerced
            if isinstance(arg, type) and isinstance(value, arg):
                return value
        return value

    if annotation in (datetime, dt_date, time):
        if isinstance(value, str):
            try:
                if annotation is datetime:
                    return datetime.fromisoformat(value)
                if annotation is dt_date:
                    return dt_date.fromisoformat(value)
                return time.fromisoformat(value)
            except ValueError:
                return value
        return value

    if annotation is UUID and isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return value

    if isinstance(annotation, type) and issubclass(annotation, Enum):
        try:
            return annotation(value)
        except ValueError:
            return value

    return value
