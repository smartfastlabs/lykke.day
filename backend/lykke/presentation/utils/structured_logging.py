"""Helpers for emitting structured logs into admin backlog."""

from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from loguru import logger

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.infrastructure.gateways import StructuredLogGateway

P = ParamSpec("P")
R = TypeVar("R")


def _coerce_json_safe(value: Any) -> Any:
    """Convert values into JSON-safe representations."""
    try:
        serialized = dataclass_to_json_dict(value)
    except Exception:
        serialized = value

    try:
        json.dumps(serialized)
        return serialized
    except TypeError:
        return str(value)


def _serialize_params(
    func: Callable[..., Awaitable[Any]], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    bound = inspect.signature(func).bind_partial(*args, **kwargs)
    return {key: _coerce_json_safe(val) for key, val in bound.arguments.items()}


async def emit_structured_log(
    *,
    event_type: str,
    event_data: dict[str, Any],
    occurred_at: datetime | None = None,
) -> None:
    """Emit a custom structured log event to the admin backlog."""
    gateway = StructuredLogGateway()
    try:
        await gateway.log_event(
            event_type=event_type,
            event_data=event_data,
            occurred_at=occurred_at,
        )
    finally:
        await gateway.close()


def structured_task(
    event_type: str = "TaskIQRun",
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator to emit structured logs for TaskIQ task runs."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            started_at = datetime.now(UTC)
            params = _serialize_params(func, args, kwargs)
            user_id = params.get("user_id")
            result: R | None = None
            error_info: dict[str, Any] | None = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as exc:
                error_info = {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                }
                raise
            finally:
                finished_at = datetime.now(UTC)
                event_data = {
                    "source": "taskiq",
                    "task": {
                        "name": func.__name__,
                        "module": func.__module__,
                    },
                    "status": "error" if error_info else "success",
                    "started_at": started_at.isoformat(),
                    "finished_at": finished_at.isoformat(),
                    "duration_ms": int(
                        (finished_at - started_at).total_seconds() * 1000
                    ),
                    "params": params,
                    "result": _coerce_json_safe(result) if error_info is None else None,
                    "error": error_info,
                }
                if user_id is not None:
                    event_data["user_id"] = str(user_id)

                try:
                    await emit_structured_log(
                        event_type=event_type,
                        event_data=event_data,
                        occurred_at=started_at,
                    )
                except Exception as exc:
                    logger.error(
                        f"Failed to emit structured task log for {func.__name__}: {exc}"
                    )

        return wrapper

    return decorator
