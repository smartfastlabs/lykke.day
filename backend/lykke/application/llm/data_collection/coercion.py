"""Coercion/validation helpers for dict -> typed dataclass fields."""

from __future__ import annotations

from dataclasses import fields as dataclass_fields, is_dataclass
from datetime import time
from enum import Enum
from typing import Any, get_args, get_origin, get_type_hints

from lykke.core.exceptions import DomainError


class DataclassCoercer:
    """Coerce partial dicts into typed dataclass field values.

    Intended for LLM tool calls like `record_fields(fields: dict[str, Any])`.
    """

    @classmethod
    def coerce_partial(
        cls,
        *,
        dataclass_type: type,
        raw: dict[str, Any],
        allowed_fields: set[str] | None = None,
    ) -> dict[str, Any]:
        if not is_dataclass(dataclass_type):
            raise DomainError(f"{dataclass_type.__name__} is not a dataclass")

        hints = get_type_hints(dataclass_type)
        if allowed_fields is None:
            allowed_fields = {f.name for f in dataclass_fields(dataclass_type)}

        coerced: dict[str, Any] = {}
        for key, value in raw.items():
            if key not in allowed_fields:
                continue
            target_type = hints.get(key)
            if target_type is None:
                coerced[key] = value
                continue
            coerced_value = cls._coerce_value(value, target_type)
            if isinstance(coerced_value, str):
                coerced_value = coerced_value.strip()
            coerced[key] = coerced_value
        return coerced

    @classmethod
    def _coerce_value(cls, value: Any, target_type: Any) -> Any:
        # Optional[T]
        origin = get_origin(target_type)
        args = get_args(target_type)
        if origin is None and isinstance(target_type, type):
            return cls._coerce_concrete(value, target_type)

        if origin is list:
            (elem_type,) = args or (Any,)
            if value is None:
                return []
            if not isinstance(value, list):
                raise DomainError("Expected list")
            return [cls._coerce_value(v, elem_type) for v in value]

        if origin is dict:
            # We keep dicts as-is; nested coercion is caller-defined.
            return value if isinstance(value, dict) else {}

        # Union / Optional
        if origin is type(None):  # pragma: no cover (defensive)
            return None
        if origin is None and args:
            # PEP604 unions sometimes land here depending on python/mypy;
            # fallback to simple union handling.
            pass

        if args:
            # Optional is Union[T, NoneType]
            if value is None:
                return None
            non_none = [a for a in args if a is not type(None)]
            last_err: Exception | None = None
            for candidate in non_none:
                try:
                    return cls._coerce_value(value, candidate)
                except Exception as exc:  # pylint: disable=broad-except
                    last_err = exc
            raise DomainError(f"Could not coerce value: {last_err}")

        return value

    @classmethod
    def _coerce_concrete(cls, value: Any, target_type: type) -> Any:
        if value is None:
            return None

        if issubclass(target_type, Enum):
            if isinstance(value, target_type):
                return value
            if isinstance(value, str):
                try:
                    return target_type(value)
                except ValueError:
                    # Numeric enums (e.g. int-based) often arrive as strings.
                    try:
                        return target_type(int(value))
                    except (ValueError, TypeError):
                        pass
                    # Try by name
                    try:
                        return target_type[value]
                    except Exception as exc:  # pylint: disable=broad-except
                        raise DomainError(str(exc)) from exc
            if isinstance(value, int):
                try:
                    return target_type(value)
                except ValueError as exc:
                    raise DomainError(str(exc)) from exc

        if target_type is time:
            if isinstance(value, time):
                return value
            if isinstance(value, str):
                try:
                    return time.fromisoformat(value)
                except ValueError as exc:
                    raise DomainError("Invalid time format (expected HH:MM)") from exc
            raise DomainError("Invalid time value")

        # Nested dataclass value objects
        from dataclasses import is_dataclass as _is_dataclass

        if _is_dataclass(target_type) and isinstance(value, dict):
            try:
                inner = cls.coerce_partial(dataclass_type=target_type, raw=value)
                return target_type(**inner)
            except TypeError as exc:
                raise DomainError(str(exc)) from exc

        if isinstance(value, target_type):
            return value
        if target_type is str:
            return str(value).strip()
        if target_type is int:
            try:
                return int(value)
            except (TypeError, ValueError) as exc:
                raise DomainError("Expected int") from exc
        if target_type is bool:
            return bool(value)

        return value

