"""Domain events related to AI chat system."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from lykke.domain.entities import AuditLogEntity
from lykke.domain.value_objects.update import (
    BotPersonalityUpdateObject,
    ConversationUpdateObject,
)

from .base import AuditedEvent, DomainEvent, EntityUpdatedEvent

__all__ = [
    "ConversationCreatedEvent",
    "ConversationUpdatedEvent",
    "MessageSentEvent",
    "FactoidCreatedEvent",
    "FactoidCriticalityUpdatedEvent",
    "BotPersonalityUpdatedEvent",
]


@dataclass(frozen=True, kw_only=True)
class ConversationCreatedEvent(DomainEvent):
    """Event raised when a new conversation is created."""

    conversation_id: UUID
    user_id: UUID
    bot_personality_id: UUID
    channel: str  # ConversationChannel enum as string


@dataclass(frozen=True, kw_only=True)
class ConversationUpdatedEvent(EntityUpdatedEvent[ConversationUpdateObject]):
    """Event raised when a conversation is updated."""


@dataclass(frozen=True, kw_only=True)
class MessageSentEvent(DomainEvent, AuditedEvent):
    """Event raised when a message is sent in a conversation."""

    message_id: UUID
    conversation_id: UUID
    role: str  # MessageRole enum as string
    content_preview: str  # First 100 chars of content

    def to_audit_log(self, user_id: UUID) -> AuditLogEntity:
        """Create audit log for message sent.

        Returns:
            AuditLogEntity for message sent.
        """
        return AuditLogEntity(
            user_id=user_id,
            activity_type=self.__class__.__name__,
            entity_id=self.message_id,
            entity_type="message",
            meta={
                "conversation_id": str(self.conversation_id),
                "role": self.role,
                "content_preview": self.content_preview,
            },
        )


@dataclass(frozen=True, kw_only=True)
class FactoidCreatedEvent(DomainEvent):
    """Event raised when a new factoid is created."""

    factoid_id: UUID
    user_id: UUID
    conversation_id: UUID | None  # None for global factoids
    factoid_type: str  # FactoidType enum as string
    criticality: str  # FactoidCriticality enum as string


@dataclass(frozen=True, kw_only=True)
class FactoidCriticalityUpdatedEvent(DomainEvent):
    """Event raised when a factoid's criticality level changes."""

    factoid_id: UUID
    old_criticality: str  # FactoidCriticality enum as string
    new_criticality: str  # FactoidCriticality enum as string
    user_confirmed: bool


@dataclass(frozen=True, kw_only=True)
class BotPersonalityUpdatedEvent(EntityUpdatedEvent[BotPersonalityUpdateObject]):
    """Event raised when a bot personality is updated."""
