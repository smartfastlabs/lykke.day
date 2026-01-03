"""Message schema."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from .base import BaseDateSchema


class Message(BaseDateSchema):
    """API schema for Message entity."""

    user_id: UUID
    author: Literal["system", "agent", "user"]
    sent_at: datetime
    content: str
    read_at: datetime | None = None

