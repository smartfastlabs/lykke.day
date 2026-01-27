"""Task override registry for worker tasks."""

from typing import Any

_TASK_OVERRIDES: dict[str, Any] = {}


def set_task_override(name: str, task: Any) -> None:
    """Override a task by name for testing."""
    _TASK_OVERRIDES[name] = task


def clear_task_overrides() -> None:
    """Clear all task overrides."""
    _TASK_OVERRIDES.clear()


def get_task(name: str, default: Any) -> Any:
    """Return an overridden task if set, otherwise the default."""
    return _TASK_OVERRIDES.get(name, default)
