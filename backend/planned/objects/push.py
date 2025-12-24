import uuid
from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from .base import BaseObject


class PushSubscription(BaseObject):
    device_name: str
    endpoint: str
    p256dh: str
    auth: str
    uuid: UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        alias="createdAt",
    )


class NotificationAction(BaseObject):
    action: str
    title: str
    icon: str | None = None


class NotificationPayload(BaseObject):
    title: str
    body: str
    icon: str | None = None
    badge: str | None = None
    tag: str | None = None
    actions: list[NotificationAction] = Field(default_factory=list)
    data: dict | None = None
