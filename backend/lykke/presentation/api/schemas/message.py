"""Message schema."""

from datetime import datetime
from typing import Any
from uuid import UUID

from .base import BaseEntitySchema, BaseSchema


class MessageSchema(BaseEntitySchema):
    """API schema for Message entity."""

    conversation_id: UUID
    role: str
    content: str
    meta: dict[str, Any] | None = None
    created_at: datetime


class SendMessageRequestSchema(BaseSchema):
    """API schema for sending a message to a conversation."""

    content: str


class SendMessageResponseSchema(BaseSchema):
    """API schema for the response after sending a message."""

    user_message: MessageSchema
    assistant_message: MessageSchema | None = None
