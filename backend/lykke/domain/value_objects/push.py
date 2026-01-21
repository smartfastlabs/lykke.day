from dataclasses import dataclass, field

from ..entities.base import BaseEntityObject


@dataclass(kw_only=True)
class NotificationAction(BaseEntityObject):
    action: str
    title: str
    icon: str | None = None


@dataclass(kw_only=True)
class NotificationPayload(BaseEntityObject):
    title: str
    body: str
    icon: str | None = None
    badge: str | None = None
    tag: str | None = None
    actions: list[NotificationAction] = field(default_factory=list)
    data: dict | None = None

