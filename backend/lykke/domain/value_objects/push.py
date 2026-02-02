from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from lykke.domain.entities.base import BaseEntityObject
from lykke.domain.value_objects.base import BaseValueObject

if TYPE_CHECKING:
    from lykke.domain.entities import (
        CalendarEntryEntity,
        PushNotificationEntity,
        RoutineEntity,
        TaskEntity,
    )


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


@dataclass(kw_only=True)
class PushNotificationContext(BaseValueObject):
    """Context payload for push notification detail views."""

    notification: "PushNotificationEntity"
    tasks: list["TaskEntity"] = field(default_factory=list)
    routines: list["RoutineEntity"] = field(default_factory=list)
    calendar_entries: list["CalendarEntryEntity"] = field(default_factory=list)
