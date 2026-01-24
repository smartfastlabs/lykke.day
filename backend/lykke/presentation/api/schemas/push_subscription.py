"""PushSubscription schema."""

from datetime import datetime
from uuid import UUID

from .base import BaseEntitySchema, BaseSchema


class PushSubscriptionSchema(BaseEntitySchema):
    """API schema for PushSubscription entity."""

    user_id: UUID
    device_name: str | None = None
    endpoint: str
    p256dh: str
    auth: str
    created_at: datetime


class PushSubscriptionUpdateSchema(BaseSchema):
    """API schema for PushSubscription update requests."""

    device_name: str | None = None


class PushSubscriptionKeysSchema(BaseSchema):
    """API schema for push subscription keys."""

    p256dh: str
    auth: str


class PushSubscriptionCreateSchema(BaseSchema):
    """API schema for PushSubscription create requests."""

    device_name: str
    endpoint: str
    keys: PushSubscriptionKeysSchema
