"""PushSubscription schema."""

from datetime import datetime
from uuid import UUID

from .base import BaseEntitySchema


class PushSubscriptionSchema(BaseEntitySchema):
    """API schema for PushSubscription entity."""

    user_id: UUID
    device_name: str | None = None
    endpoint: str
    p256dh: str
    auth: str
    created_at: datetime

