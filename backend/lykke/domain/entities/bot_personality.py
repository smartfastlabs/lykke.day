"""Bot personality entity for AI chatbot system."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from lykke.domain.events.ai_chat_events import BotPersonalityUpdatedEvent
from lykke.domain.value_objects.update import BotPersonalityUpdateObject

from .base import BaseEntityObject


@dataclass(kw_only=True)
class BotPersonalityEntity(
    BaseEntityObject[BotPersonalityUpdateObject, BotPersonalityUpdatedEvent]
):
    """Bot personality entity representing an AI bot personality configuration."""

    user_id: UUID | None  # None for system defaults
    name: str
    base_bot_personality_id: UUID | None  # Inherits from base
    system_prompt: str
    user_amendments: str = ""  # User customizations
    meta: dict = field(default_factory=dict)  # Additional config
    created_at: datetime

    def get_full_prompt(self) -> str:
        """Get the full system prompt including amendments.

        Returns:
            Combined system_prompt and user_amendments
        """
        if self.user_amendments:
            return f"{self.system_prompt}\n\n{self.user_amendments}"
        return self.system_prompt

    def is_system_default(self) -> bool:
        """Check if this is a system default personality.

        Returns:
            True if user_id is None (system-provided)
        """
        return self.user_id is None
