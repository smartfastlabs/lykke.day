"""Event handler that triggers smart notification evaluation on task status changes."""

from typing import ClassVar

from loguru import logger

from lykke.application.events.handlers.base import DomainEventHandler
from lykke.domain.events.base import DomainEvent
from lykke.domain.events.task_events import (
    TaskCompletedEvent,
    TaskPuntedEvent,
    TaskStatusChangedEvent,
)


class SmartNotificationTriggerHandler(DomainEventHandler):
    """Triggers smart notification evaluation when task status changes.

    This handler enqueues a background task to evaluate whether a notification
    should be sent. It runs asynchronously and doesn't block the transaction.
    """

    handles: ClassVar[list[type[DomainEvent]]] = [
        TaskCompletedEvent,
        TaskStatusChangedEvent,
        TaskPuntedEvent,
    ]

    async def handle(self, event: DomainEvent) -> None:
        """Handle task status change events by enqueuing notification evaluation.

        Args:
            event: The task status change event
        """
        user_id = self.user_id

        # Determine trigger type from event
        if isinstance(event, TaskCompletedEvent):
            triggered_by = "task_completed"
        elif isinstance(event, TaskPuntedEvent):
            triggered_by = "task_punted"
        elif isinstance(event, TaskStatusChangedEvent):
            triggered_by = "task_status_changed"
        else:
            triggered_by = "task_event"

        # Enqueue background task to evaluate notification
        # This runs asynchronously and doesn't block the transaction
        try:
            from lykke.presentation.workers import tasks as worker_tasks

            task = worker_tasks.get_task(
                "evaluate_smart_notification_task",
                worker_tasks.evaluate_smart_notification_task,
            )
            await task.kiq(
                user_id=user_id,
                triggered_by=triggered_by,
            )
            logger.debug(
                f"Enqueued smart notification evaluation for user {user_id} "
                f"(triggered by {triggered_by})"
            )
        except Exception as e:
            # Log but don't fail - this is a background task
            logger.error(
                f"Failed to enqueue smart notification evaluation for user {user_id}: {e}"
            )
