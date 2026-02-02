"""Command to store inbound SMS messages."""

from dataclasses import dataclass
from typing import Any

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.worker_schedule import get_current_workers_to_schedule
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity
from lykke.domain.events.ai_chat_events import MessageReceivedEvent


@dataclass(frozen=True)
class ReceiveSmsMessageCommand(Command):
    """Command to persist an inbound SMS message."""

    from_number: str
    to_number: str | None
    body: str
    payload: dict[str, Any]


class ReceiveSmsMessageHandler(
    BaseCommandHandler[ReceiveSmsMessageCommand, MessageEntity]
):
    """Persist an inbound SMS message and emit domain events."""

    async def handle(self, command: ReceiveSmsMessageCommand) -> MessageEntity:
        """Store the inbound message and emit domain events."""
        async with self.new_uow() as uow:
            message = MessageEntity(
                user_id=self.user_id,
                role=value_objects.MessageRole.USER,
                type=value_objects.MessageType.SMS_INBOUND,
                content=command.body,
                meta={
                    "provider": "twilio",
                    "from_number": command.from_number,
                    "to_number": command.to_number,
                    "payload": command.payload,
                },
                triggered_by="sms_inbound",
            )
            message.create()
            message.add_event(
                MessageReceivedEvent(
                    user_id=self.user_id,
                    message_id=message.id,
                    role=message.role.value,
                    content_preview=message.get_content_preview(),
                )
            )

            uow.add(message)

            workers_to_schedule = get_current_workers_to_schedule()
            if workers_to_schedule is None:
                logger.warning(
                    f"No post-commit worker scheduler available for user {self.user_id} message {message.id}",
                )
                return message

            from lykke.presentation.workers import tasks as worker_tasks

            worker = worker_tasks.get_worker(worker_tasks.process_inbound_sms_message_task)
            workers_to_schedule.schedule(
                worker, user_id=self.user_id, message_id=message.id
            )

            return message
