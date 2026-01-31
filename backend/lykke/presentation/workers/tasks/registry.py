"""Worker override registry for background workers."""

from collections.abc import Callable
from typing import Any

_WORKER_OVERRIDES: dict[str, Any] = {}


def set_worker_override(name: str | Callable[..., Any], worker: Any) -> None:
    """Override a worker by name or by function (uses __name__) for testing."""
    key = name if isinstance(name, str) else name.__name__
    _WORKER_OVERRIDES[key] = worker


def clear_worker_overrides() -> None:
    """Clear all worker overrides."""
    _WORKER_OVERRIDES.clear()


def get_worker(worker: Callable[..., Any]) -> Any:
    """Return an overridden worker if set, otherwise the given worker."""
    return _WORKER_OVERRIDES.get(worker.__name__, worker)


class WorkerRegistry:
    """Injectable registry that resolves workers with override support."""

    def get_worker(self, worker: Callable[..., Any]) -> Any:
        """Return the worker, or an override if set (for testing)."""
        return get_worker(worker)
