"""Conversation schema."""

from datetime import datetime
from typing import Any
from uuid import UUID

from .base import BaseEntitySchema


class ConversationSchema(BaseEntitySchema):
    """API schema for Conversation entity."""

    user_id: UUID
    bot_personality_id: UUID
    channel: str
    status: str
    llm_provider: str
    context: dict[str, Any] | None = None
    created_at: datetime
    last_message_at: datetime
