"""Message entity for AI chatbot system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime
from typing import Any, cast
from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.events.ai_chat_events import MessageLLMRunRecordedEvent

from .base import BaseEntityObject
from .has_date import HasDateMixin


@dataclass(kw_only=True)
class MessageEntity(HasDateMixin, BaseEntityObject):
    """Message entity representing a single message."""

    user_id: UUID
    role: value_objects.MessageRole
    type: value_objects.MessageType = value_objects.MessageType.UNKNOWN
    content: str
    meta: dict[str, Any] = field(default_factory=dict)  # Provider-specific metadata
    llm_run_result: value_objects.LLMRunResultSnapshot | None = None
    triggered_by: str | None = None
    date: dt_date = field(default=None)  # type: ignore[assignment]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        current_date = cast(dt_date | None, object.__getattribute__(self, "date"))
        if current_date is None:
            self.date = self.created_at.date()
        self.resolve_day_id()

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

    def update_llm_run_result(
        self, result: value_objects.LLMRunResultSnapshot
    ) -> MessageEntity:
        """Store the LLM run result snapshot for this message."""
        if self.llm_run_result == result:
            return self
        updated = self.clone(llm_run_result=result)
        updated._add_event(
            MessageLLMRunRecordedEvent(
                user_id=self.user_id,
                message_id=self.id,
                entity_id=self.id,
                entity_type="message",
            )
        )
        return updated
