"""Demo event handler that logs task status changes."""

from loguru import logger

from lykke.domain.events.base import DomainEvent
from lykke.domain.events.task_events import (
    TaskCompletedEvent,
    TaskStatusChangedEvent,
)

from .base import DomainEventHandler


class TaskStatusLoggerHandler(DomainEventHandler):
    """Logs all task status change events.

    This is a demo handler showing how to react to domain events.
    Real handlers could:
    - Send push notifications
    - Update analytics/metrics
    - Trigger downstream workflows
    - Sync with external systems
    """

    handles = [TaskStatusChangedEvent, TaskCompletedEvent]

    async def handle(self, event: DomainEvent) -> None:
        """Log task status changes."""
        if isinstance(event, TaskStatusChangedEvent):
            logger.info(
                f"📋 Task {event.task_id} status changed: "
                f"{event.old_status} → {event.new_status}"
            )
        elif isinstance(event, TaskCompletedEvent):
            logger.info(
                f"✅ Task {event.task_id} completed at {event.completed_at}"
            )

