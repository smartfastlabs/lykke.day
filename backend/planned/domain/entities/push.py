import uuid
from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from .base import BaseConfigObject


class PushSubscription(BaseConfigObject):
    device_name: str | None = None
    endpoint: str
    p256dh: str
    auth: str
    uuid: UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        alias="createdAt",
    )


class NotificationAction(BaseConfigObject):
    action: str
    title: str
    icon: str | None = None


class NotificationPayload(BaseConfigObject):
    title: str
    body: str
    icon: str | None = None
    badge: str | None = None
    tag: str | None = None
    actions: list[NotificationAction] = Field(default_factory=list)
    data: dict | None = None
