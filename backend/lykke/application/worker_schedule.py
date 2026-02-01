"""Protocols for post-commit worker scheduling after UOW commit."""

from collections.abc import Callable
from contextvars import ContextVar, Token
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


_current_workers_to_schedule: ContextVar[WorkersToScheduleProtocol | None] = (
    ContextVar("current_workers_to_schedule", default=None)
)


def get_current_workers_to_schedule() -> WorkersToScheduleProtocol | None:
    """Return the UOW-scoped workers-to-schedule instance if present."""
    return _current_workers_to_schedule.get()


def set_current_workers_to_schedule(
    workers: WorkersToScheduleProtocol,
) -> Token[WorkersToScheduleProtocol | None]:
    """Set the current workers-to-schedule instance for this context."""
    return _current_workers_to_schedule.set(workers)


def reset_current_workers_to_schedule(
    token: Token[WorkersToScheduleProtocol | None],
) -> None:
    """Reset the current workers-to-schedule instance to its previous state."""
    _current_workers_to_schedule.reset(token)
