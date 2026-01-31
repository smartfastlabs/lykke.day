"""Event handler that triggers inbound SMS processing on receipt."""

from typing import ClassVar

from loguru import logger

from lykke.application.events.handlers.base import DomainEventHandler
from lykke.domain.events.ai_chat_events import MessageReceivedEvent
from lykke.domain.events.base import DomainEvent


class InboundSmsProcessingTriggerHandler(DomainEventHandler):
    """Triggers async inbound SMS processing when a new SMS message is received."""

    handles: ClassVar[list[type[DomainEvent]]] = [MessageReceivedEvent]

    async def handle(self, event: DomainEvent) -> None:
        """Handle new inbound messages by enqueuing processing."""
        if not isinstance(event, MessageReceivedEvent):
            return

        try:
            from lykke.presentation.workers import tasks as worker_tasks

            worker = worker_tasks.get_worker(
                worker_tasks.process_inbound_sms_message_task
            )
            await worker.kiq(user_id=event.user_id, message_id=event.message_id)
            logger.debug(
                "Enqueued inbound SMS processing for user %s message %s",
                event.user_id,
                event.message_id,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "Failed to enqueue inbound SMS processing for user %s: %s",
                event.user_id,
                exc,
            )
