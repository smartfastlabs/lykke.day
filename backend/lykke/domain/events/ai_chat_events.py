"""Domain events related to AI chat system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lykke.domain.value_objects.update import (
    BotPersonalityUpdateObject,
    FactoidUpdateObject,
)

from .base import AuditableDomainEvent, DomainEvent, EntityUpdatedEvent

if TYPE_CHECKING:
    from uuid import UUID

__all__ = [
    "BotPersonalityUpdatedEvent",
    "FactoidCreatedEvent",
    "FactoidCriticalityUpdatedEvent",
    "FactoidUpdatedEvent",
    "MessageLLMRunRecordedEvent",
    "MessageReceivedEvent",
    "MessageSentEvent",
]


@dataclass(frozen=True, kw_only=True)
class MessageSentEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a message is sent.

    Uses AuditableDomainEvent: User sent a message to the system.
    """

    message_id: UUID
    role: str  # MessageRole enum as string
    content_preview: str  # First 100 chars of content

    def __post_init__(self) -> None:
        if self.entity_id is None:
            object.__setattr__(self, "entity_id", self.message_id)
        if self.entity_type is None:
            object.__setattr__(self, "entity_type", "message")


@dataclass(frozen=True, kw_only=True)
class MessageReceivedEvent(DomainEvent, AuditableDomainEvent):
    """Event raised when a message is received.

    Uses AuditableDomainEvent: User sent a message to the system (via SMS or other inbound channels).
    This is a deliberate user action and should appear in the activity timeline.
    """

    message_id: UUID
    role: str  # MessageRole enum as string
    content_preview: str  # First 100 chars of content

    def __post_init__(self) -> None:
        if self.entity_id is None:
            object.__setattr__(self, "entity_id", self.message_id)
        if self.entity_type is None:
            object.__setattr__(self, "entity_type", "message")


@dataclass(frozen=True, kw_only=True)
class MessageLLMRunRecordedEvent(DomainEvent):
    """Event raised when an LLM run result is stored for a message."""

    message_id: UUID


@dataclass(frozen=True, kw_only=True)
class FactoidCreatedEvent(DomainEvent):
    """Event raised when a new factoid is created."""

    factoid_id: UUID
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
