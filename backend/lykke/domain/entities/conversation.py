"""Conversation entity for AI chatbot system."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.events.ai_chat_events import ConversationUpdatedEvent
from lykke.domain.value_objects.update import ConversationUpdateObject

from .base import BaseEntityObject


@dataclass(kw_only=True)
class ConversationEntity(
    BaseEntityObject[ConversationUpdateObject, ConversationUpdatedEvent]
):
    """Conversation entity representing an AI chat conversation."""

    user_id: UUID
    bot_personality_id: UUID
    channel: value_objects.ConversationChannel
    status: value_objects.ConversationStatus
    llm_provider: value_objects.LLMProvider
    context: dict = field(default_factory=dict)  # Conversation-specific metadata
    created_at: datetime
    last_message_at: datetime

    def update_last_message_time(self) -> "ConversationEntity":
        """Update the last_message_at timestamp to now."""
        return self.clone(last_message_at=datetime.now(UTC))

    def archive(self) -> "ConversationEntity":
        """Archive this conversation."""
        return self.clone(status=value_objects.ConversationStatus.ARCHIVED)

    def pause(self) -> "ConversationEntity":
        """Pause this conversation."""
        return self.clone(status=value_objects.ConversationStatus.PAUSED)

    def resume(self) -> "ConversationEntity":
        """Resume this conversation."""
        return self.clone(status=value_objects.ConversationStatus.ACTIVE)
