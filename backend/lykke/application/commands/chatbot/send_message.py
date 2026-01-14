"""Command to send a message to a conversation and optionally receive a response."""

from uuid import UUID

from loguru import logger
from lykke.application.commands.base import BaseCommandHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import ConversationEntity, MessageEntity


class SendMessageHandler(BaseCommandHandler):
    """Handles sending a message to a conversation and generating an optional response.

    This handler:
    1. Loads the conversation
    2. Creates and persists the user message
    3. Generates a dummy assistant response (no LLM for now)
    4. Persists the assistant message if a response is generated
    5. Updates the conversation's last_message_at timestamp
    """

    async def run(
        self, conversation_id: UUID, content: str
    ) -> tuple[MessageEntity, MessageEntity | None]:
        """Send a message and optionally receive a response.

        Args:
            conversation_id: The ID of the conversation to send the message to
            content: The content of the message to send

        Returns:
            Tuple of (user_message, assistant_message_or_none)

        Raises:
            NotFoundError: If the conversation doesn't exist
        """
        logger.info(
            f"Sending message to conversation {conversation_id} for user {self.user_id}"
        )

        # Load the conversation
        conversation = await self.conversation_ro_repo.get(conversation_id)

        # Create user message entity
        user_message = MessageEntity(
            conversation_id=conversation_id,
            role=value_objects.MessageRole.USER,
            content=content,
        )

        # Generate dummy assistant response (placeholder for LLM integration)
        assistant_message = self._generate_dummy_response(
            conversation=conversation, user_message=user_message
        )

        # Persist messages and update conversation
        async with self.new_uow() as uow:
            # Save user message
            await uow.create(user_message)
            logger.info(f"Persisted user message {user_message.id}")

            # Save assistant message if generated
            if assistant_message:
                await uow.create(assistant_message)
                logger.info(f"Persisted assistant message {assistant_message.id}")

            # Update conversation's last_message_at timestamp
            updated_conversation = conversation.update_last_message_time()
            uow.add(updated_conversation)
            logger.info(f"Updated conversation {conversation_id} last_message_at")

        return user_message, assistant_message

    def _generate_dummy_response(
        self, conversation: ConversationEntity, user_message: MessageEntity
    ) -> MessageEntity | None:
        """Generate a dummy response (placeholder for LLM integration).

        Args:
            conversation: The conversation entity
            user_message: The user's message

        Returns:
            An optional assistant message entity
        """
        # For now, return a simple canned response 50% of the time
        # In the future, this will be replaced with actual LLM integration
        import random

        if random.random() < 0.5:
            return MessageEntity(
                conversation_id=conversation.id,
                role=value_objects.MessageRole.ASSISTANT,
                content=f"I received your message: '{user_message.content}'. This is a dummy response - LLM integration coming soon!",
            )

        # Sometimes return no response
        return None
