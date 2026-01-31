"""Command to store inbound SMS messages."""

from dataclasses import dataclass
from typing import Any

from lykke.application.commands.base import BaseCommandHandler, Command
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

            return message
