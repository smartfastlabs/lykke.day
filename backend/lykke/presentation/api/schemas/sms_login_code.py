"""SmsLoginCode schema."""

from datetime import datetime
from uuid import UUID

from .base import BaseEntitySchema


class SmsLoginCodeSchema(BaseEntitySchema):
    """API schema for SmsLoginCode entity."""

    user_id: UUID
    phone_number: str
    code_hash: str
    expires_at: datetime
    consumed_at: datetime | None = None
    created_at: datetime
    attempt_count: int
    last_attempt_at: datetime | None = None
