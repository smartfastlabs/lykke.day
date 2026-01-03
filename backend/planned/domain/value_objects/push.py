from dataclasses import dataclass, field

from ..entities.base import BaseConfigObject


@dataclass(kw_only=True)
class NotificationAction(BaseConfigObject):
    action: str
    title: str
    icon: str | None = None


@dataclass(kw_only=True)
class NotificationPayload(BaseConfigObject):
    title: str
    body: str
    icon: str | None = None
    badge: str | None = None
    tag: str | None = None
    actions: list[NotificationAction] = field(default_factory=list)
    data: dict | None = None

