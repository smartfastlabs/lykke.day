"""Protocols for post-commit worker scheduling after UOW commit."""

from collections.abc import Callable
from typing import Any, Protocol


class WorkersToScheduleProtocol(Protocol):
    """Protocol for UOW-scoped collection of workers to schedule after commit."""

    def schedule(self, worker: Callable[..., Any], **kwargs: Any) -> None:
        """Add a worker to be sent to the broker after commit.

        Args:
            worker: The taskiq worker (callable with .kiq method).
            **kwargs: Arguments to pass to worker.kiq().
        """
        ...

    async def flush(self) -> None:
        """Send all scheduled workers to the broker. Called by UOW after commit."""
        ...


class WorkerRegistryProtocol(Protocol):
    """Protocol for resolving workers (supports test overrides via get_worker)."""

    def get_worker(self, worker: Callable[..., Any]) -> Any:
        """Return the worker, or an override if set (for testing).

        Args:
            worker: The default worker (used for lookup by __name__ and as fallback).

        Returns:
            The worker to use (override or default).
        """
        ...


class NoOpWorkersToSchedule:
    """No-op implementation when worker scheduling is not configured."""

    def schedule(self, worker: Callable[..., Any], **kwargs: Any) -> None:
        """No-op."""

    async def flush(self) -> None:
        """No-op."""
