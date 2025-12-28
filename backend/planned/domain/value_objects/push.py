from pydantic import Field

from ..entities.base import BaseConfigObject


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

