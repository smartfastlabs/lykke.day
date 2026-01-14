"""Calendar schema."""

from datetime import datetime
from uuid import UUID

from lykke.domain.value_objects.task import EventCategory

from .base import BaseEntitySchema, BaseSchema


class SyncSubscriptionSchema(BaseSchema):
    """Schema describing a calendar sync subscription."""

    subscription_id: str
    resource_id: str | None = None
    expiration: datetime
    provider: str
    client_state: str | None = None
    sync_token: str | None = None
    webhook_url: str | None = None


class CalendarCreateSchema(BaseSchema):
    """API schema for creating a Calendar entity."""

    name: str
    auth_token_id: UUID
    platform_id: str
    platform: str
    last_sync_at: datetime | None = None
    default_event_category: EventCategory | None = None


class CalendarSchema(CalendarCreateSchema, BaseEntitySchema):
    """API schema for Calendar entity."""

    user_id: UUID
    sync_subscription: SyncSubscriptionSchema | None = None
    sync_subscription_id: str | None = None
    sync_enabled: bool = False


class CalendarUpdateSchema(BaseSchema):
    """API schema for Calendar update requests."""

    name: str | None = None
    auth_token_id: UUID | None = None
    default_event_category: EventCategory | None = None
    last_sync_at: datetime | None = None

