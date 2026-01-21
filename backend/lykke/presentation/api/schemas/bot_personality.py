"""Bot personality schema."""

from datetime import datetime
from typing import Any
from uuid import UUID

from .base import BaseEntitySchema


class BotPersonalitySchema(BaseEntitySchema):
    """Schema for BotPersonality entity."""

    user_id: UUID | None = None
    name: str
    base_bot_personality_id: UUID | None = None
    system_prompt: str
    user_amendments: str = ""
    meta: dict[str, Any] = {}
    created_at: datetime
