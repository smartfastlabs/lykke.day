"""Event handler that triggers brain dump processing on new items."""

from typing import ClassVar

from loguru import logger

from lykke.application.events.handlers.base import DomainEventHandler
from lykke.domain.events.base import DomainEvent
from lykke.domain.events.day_events import BrainDumpAddedEvent


class BrainDumpProcessingTriggerHandler(DomainEventHandler):
    """Triggers async brain dump processing when a new item is added."""

    handles: ClassVar[list[type[DomainEvent]]] = [BrainDumpAddedEvent]

    async def handle(self, event: DomainEvent) -> None:
        """Handle new brain dump items by enqueuing processing."""
        if not isinstance(event, BrainDumpAddedEvent):
            return

        try:
            from lykke.presentation.workers import tasks as worker_tasks

            worker = worker_tasks.get_worker(worker_tasks.process_brain_dump_item_task)
            await worker.kiq(
                user_id=event.user_id,
                day_date=event.date.isoformat(),
                item_id=event.item_id,
            )
            logger.debug(
                "Enqueued brain dump processing for user %s item %s",
                event.user_id,
                event.item_id,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "Failed to enqueue brain dump processing for user %s: %s",
                event.user_id,
                exc,
            )
