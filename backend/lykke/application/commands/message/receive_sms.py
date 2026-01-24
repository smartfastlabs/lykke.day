"""Command to store inbound SMS messages."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity
from lykke.domain.events.ai_chat_events import MessageReceivedEvent


@dataclass(frozen=True)
class ReceiveSmsMessageCommand(Command):
    """Command to persist an inbound SMS message for a conversation."""

    conversation_id: UUID
    from_number: str
    to_number: str | None
    body: str
    payload: dict[str, Any]


class ReceiveSmsMessageHandler(
    BaseCommandHandler[ReceiveSmsMessageCommand, MessageEntity]
):
    """Persist an inbound SMS message and emit domain events."""

    async def handle(self, command: ReceiveSmsMessageCommand) -> MessageEntity:
        """Store the inbound message and update conversation timestamps."""
        async with self.new_uow() as uow:
            conversation = await uow.conversation_ro_repo.get(command.conversation_id)

            message = MessageEntity(
                user_id=conversation.user_id,
                conversation_id=conversation.id,
                role=value_objects.MessageRole.USER,
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
                    user_id=conversation.user_id,
                    message_id=message.id,
                    conversation_id=message.conversation_id,
                    role=message.role.value,
                    content_preview=message.get_content_preview(),
                )
            )

            updated_conversation = conversation.update_last_message_time()

            uow.add(message)
            uow.add(updated_conversation)

            return message
