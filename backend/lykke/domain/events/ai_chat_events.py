"""Domain events related to AI chat system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.domain.value_objects.update import (
    BotPersonalityUpdateObject,
    ConversationUpdateObject,
    FactoidUpdateObject,
)

from .base import AuditableDomainEvent, DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from uuid import UUID

__all__ = [
    "BotPersonalityUpdatedEvent",
    "ConversationCreatedEvent",
    "ConversationUpdatedEvent",
    "FactoidCreatedEvent",
    "FactoidCriticalityUpdatedEvent",
    "FactoidUpdatedEvent",
    "MessageReceivedEvent",
    "MessageSentEvent",
]


@dataclass(frozen=True, kw_only=True)
class ConversationCreatedEvent(DomainEvent):
    """Event raised when a new conversation is created."""

    conversation_id: UUID
    bot_personality_id: UUID
    channel: str  # ConversationChannel enum as string


@dataclass(frozen=True, kw_only=True)
class ConversationUpdatedEvent(EntityUpdatedEvent[ConversationUpdateObject]):
    """Event raised when a conversation is updated."""


@dataclass(frozen=True, kw_only=True)
class MessageSentEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a message is sent in a conversation.

    Uses AuditableDomainEvent: User sent a message in AI chat conversation,
    this is a deliberate user action that represents engagement with the AI.
    Important for conversation history and context.
    """

    message_id: UUID
    conversation_id: UUID
    role: str  # MessageRole enum as string
    content_preview: str  # First 100 chars of content


@dataclass(frozen=True, kw_only=True)
class MessageReceivedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a message is received in a conversation.

    Uses AuditableDomainEvent: User sent a message to the system (via SMS or other
    inbound channels). This is a deliberate user action and should appear in
    the activity timeline.
    """

    message_id: UUID
    conversation_id: UUID
    role: str  # MessageRole enum as string
    content_preview: str  # First 100 chars of content


@dataclass(frozen=True, kw_only=True)
class FactoidCreatedEvent(DomainEvent):
    """Event raised when a new factoid is created."""

    factoid_id: UUID
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
class FactoidUpdatedEvent(EntityUpdatedEvent[FactoidUpdateObject]):
    """Event raised when a factoid is updated via apply_update()."""


@dataclass(frozen=True, kw_only=True)
class BotPersonalityUpdatedEvent(EntityUpdatedEvent[BotPersonalityUpdateObject]):
    """Event raised when a bot personality is updated."""
