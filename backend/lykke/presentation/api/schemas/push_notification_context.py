"""Push notification context schema."""

from pydantic import Field

from .base import BaseSchema
from .calendar_entry import CalendarEntrySchema
from .push_notification import PushNotificationSchema
from .routine import RoutineSchema
from .task import TaskSchema


class PushNotificationContextSchema(BaseSchema):
    """API schema for push notification context."""

    notification: PushNotificationSchema
    tasks: list[TaskSchema] = Field(default_factory=list)
    routines: list[RoutineSchema] = Field(default_factory=list)
    calendar_entries: list[CalendarEntrySchema] = Field(default_factory=list)
