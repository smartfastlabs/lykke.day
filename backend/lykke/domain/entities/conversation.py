"""Conversation entity for AI chatbot system."""

# pylint: disable=protected-access,no-member
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
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
    status: value_objects.ConversationStatus = value_objects.ConversationStatus.ACTIVE
    llm_provider: value_objects.LLMProvider = value_objects.LLMProvider.ANTHROPIC
    context: dict[str, Any] = field(
        default_factory=dict
    )  # Conversation-specific metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_message_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_last_message_time(self) -> "ConversationEntity":
        """Update the last_message_at timestamp to now."""
        updated = self.clone(last_message_at=datetime.now(UTC))
        # Add update event with empty update object since last_message_at
        # is an internal timestamp field not exposed in the update object
        updated._add_event(
            ConversationUpdatedEvent(
                update_object=ConversationUpdateObject(), user_id=self.user_id
            )
        )
        return updated

    def archive(self) -> "ConversationEntity":
        """Archive this conversation."""
        updated = self.clone(status=value_objects.ConversationStatus.ARCHIVED)
        updated._add_event(
            ConversationUpdatedEvent(
                update_object=ConversationUpdateObject(
                    status=value_objects.ConversationStatus.ARCHIVED.value
                ),
                user_id=self.user_id,
            )
        )
        return updated

    def pause(self) -> "ConversationEntity":
        """Pause this conversation."""
        updated = self.clone(status=value_objects.ConversationStatus.PAUSED)
        updated._add_event(
            ConversationUpdatedEvent(
                update_object=ConversationUpdateObject(
                    status=value_objects.ConversationStatus.PAUSED.value
                ),
                user_id=self.user_id,
            )
        )
        return updated

    def resume(self) -> "ConversationEntity":
        """Resume this conversation."""
        updated = self.clone(status=value_objects.ConversationStatus.ACTIVE)
        updated._add_event(
            ConversationUpdatedEvent(
                update_object=ConversationUpdateObject(
                    status=value_objects.ConversationStatus.ACTIVE.value
                ),
                user_id=self.user_id,
            )
        )
        return updated
