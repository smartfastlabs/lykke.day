"""Post-commit workers-to-schedule implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger

from lykke.application.worker_schedule import WorkerRegistryProtocol


class WorkersToSchedule:
    """UOW-scoped collection of workers to schedule after commit."""

    def __init__(self, worker_registry: WorkerRegistryProtocol) -> None:
        self._worker_registry = worker_registry
        self._pending: list[tuple[Any, dict[str, Any]]] = []

    def schedule(self, worker: Callable[..., Any], **kwargs: Any) -> None:
        """Add a worker to be sent to the broker after commit."""
        resolved = self._worker_registry.get_worker(worker)
        self._pending.append((resolved, kwargs))

    async def flush(self) -> None:
        """Send all scheduled workers to the broker."""
        for resolved_worker, kwargs in self._pending:
            try:
                await resolved_worker.kiq(**kwargs)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "Failed to schedule worker %s: %s",
                    getattr(resolved_worker, "task_name", resolved_worker),
                    exc,
                )
        self._pending.clear()
