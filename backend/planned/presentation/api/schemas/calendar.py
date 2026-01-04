"""Calendar schema."""

from datetime import datetime
from uuid import UUID

from .base import BaseEntitySchema, BaseSchema


class CalendarSchema(BaseEntitySchema):
    """API schema for Calendar entity."""

    user_id: UUID
    name: str
    auth_token_id: UUID
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None


class CalendarUpdateSchema(BaseSchema):
    """API schema for Calendar update requests."""

    name: str | None = None
    auth_token_id: UUID | None = None
    last_sync_at: datetime | None = None

