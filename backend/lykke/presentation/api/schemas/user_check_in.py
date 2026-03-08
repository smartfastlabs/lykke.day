"""User check-in API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from lykke.domain.value_objects.user_check_in import UserCheckInSource

from .base import BaseEntitySchema, BaseSchema


class UserCheckInSchema(BaseEntitySchema):
    """API schema for UserCheckIn entity."""

    user_id: UUID
    source: UserCheckInSource
    source_name: str | None = None
    source_metadata: dict[str, Any] = {}
    checkin_at: datetime
    created_at: datetime
    text: str | None = None
    scores: dict[str, Any] = {}


class UserCheckInCreateSchema(BaseSchema):
    """API schema for creating a user check-in (user-authored)."""

    text: str | None = None
    scores: dict[str, float | int] | None = None
    checkin_at: datetime | None = None
