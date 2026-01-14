"""Domain events related to AI chat system."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from lykke.domain.value_objects.update import (
    BotPersonalityUpdateObject,
    ConversationUpdateObject,
)

from .base import AuditedEvent, DomainEvent, EntityUpdatedEvent

__all__ = [
    "BotPersonalityUpdatedEvent",
    "ConversationCreatedEvent",
    "ConversationUpdatedEvent",
    "FactoidCreatedEvent",
    "FactoidCriticalityUpdatedEvent",
    "MessageSentEvent",
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
