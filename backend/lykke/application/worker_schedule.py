"""Protocols for post-commit worker scheduling after UOW commit."""

from contextvars import ContextVar, Token
from typing import Protocol
from uuid import UUID


class WorkersToScheduleProtocol(Protocol):
    """Protocol for UOW-scoped collection of workers to schedule after commit."""

    def schedule_process_brain_dump_item(
        self, *, user_id: UUID, day_date: str, item_id: UUID
    ) -> None:
        """Schedule post-commit processing for a brain dump item."""
        pass

    def schedule_process_inbound_sms_message(
        self, *, user_id: UUID, message_id: UUID
    ) -> None:
        """Schedule post-commit processing for an inbound SMS message."""
        pass

    async def flush(self) -> None:
        """Send all scheduled workers to the broker. Called by UOW after commit."""
        pass


class NoOpWorkersToSchedule:
    """No-op implementation when worker scheduling is not configured."""

    def schedule_process_brain_dump_item(
        self, *, user_id: UUID, day_date: str, item_id: UUID
    ) -> None:
        """No-op."""
        _ = (user_id, day_date, item_id)

    def schedule_process_inbound_sms_message(
        self, *, user_id: UUID, message_id: UUID
    ) -> None:
        """No-op."""
        _ = (user_id, message_id)

    async def flush(self) -> None:
        """No-op."""


_current_workers_to_schedule: ContextVar[WorkersToScheduleProtocol | None] = ContextVar(
    "current_workers_to_schedule", default=None
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
