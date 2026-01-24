"""Message entity for AI chatbot system."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from lykke.domain import value_objects

from .base import BaseEntityObject


@dataclass(kw_only=True)
class MessageEntity(BaseEntityObject):
    """Message entity representing a single message in a conversation."""

    user_id: UUID | None = None
    conversation_id: UUID
    role: value_objects.MessageRole
    content: str
    meta: dict[str, Any] = field(default_factory=dict)  # Provider-specific metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def get_content_preview(self, max_length: int = 100) -> str:
        """Get a preview of the message content.

        Args:
            max_length: Maximum length of the preview

        Returns:
            Truncated content with ellipsis if needed
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."
