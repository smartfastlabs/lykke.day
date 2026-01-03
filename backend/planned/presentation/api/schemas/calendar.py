"""Calendar schema."""

from datetime import datetime
from uuid import UUID

from .base import BaseEntitySchema


class Calendar(BaseEntitySchema):
    """API schema for Calendar entity."""

    user_id: UUID
    name: str
    auth_token_id: UUID
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None

