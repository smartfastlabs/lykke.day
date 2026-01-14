"""Factoid entity for AI chatbot system."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.events.ai_chat_events import FactoidCriticalityUpdatedEvent

from .base import BaseEntityObject


@dataclass(kw_only=True)
class FactoidEntity(BaseEntityObject):
    """Factoid entity representing a piece of information stored from conversations."""

    user_id: UUID
    conversation_id: UUID | None = None  # None for global factoids
    factoid_type: value_objects.FactoidType
    criticality: value_objects.FactoidCriticality = value_objects.FactoidCriticality.NORMAL
    content: str
    embedding: list[float] | None = None  # Vector embedding for semantic search
    ai_suggested: bool = False  # AI marked as important
    user_confirmed: bool = False  # User confirmed criticality
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    access_count: int = 0
    meta: dict[str, Any] = field(default_factory=dict)  # Additional metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_global(self) -> bool:
        """Check if this is a global factoid (not tied to a specific conversation).

        Returns:
            True if conversation_id is None
        """
        return self.conversation_id is None

    def access(self) -> "FactoidEntity":
        """Record access to this factoid.

        Updates last_accessed timestamp and increments access_count.

        Returns:
            Updated entity
        """
        return self.clone(
            last_accessed=datetime.now(UTC),
            access_count=self.access_count + 1,
        )

    def update_criticality(
        self,
        new_criticality: value_objects.FactoidCriticality,
        user_confirmed: bool = False,
    ) -> "FactoidEntity":
        """Update the criticality level of this factoid.

        Args:
            new_criticality: New criticality level
            user_confirmed: Whether the user explicitly confirmed this level

        Returns:
            Updated entity with criticality updated event
        """
        old_criticality = self.criticality
        updated_entity = self.clone(
            criticality=new_criticality,
            user_confirmed=user_confirmed or self.user_confirmed,
        )

        # Add domain event
        updated_entity._add_event(
            FactoidCriticalityUpdatedEvent(
                factoid_id=self.id,
                old_criticality=old_criticality.value,
                new_criticality=new_criticality.value,
                user_confirmed=user_confirmed,
            )
        )

        return updated_entity

    def mark_ai_suggested(self) -> "FactoidEntity":
        """Mark this factoid as AI-suggested for importance.

        Returns:
            Updated entity
        """
        return self.clone(ai_suggested=True)

    def is_important_or_critical(self) -> bool:
        """Check if this factoid is important or critical.

        Returns:
            True if criticality is important or critical
        """
        return self.criticality in (
            value_objects.FactoidCriticality.IMPORTANT,
            value_objects.FactoidCriticality.CRITICAL,
        )
