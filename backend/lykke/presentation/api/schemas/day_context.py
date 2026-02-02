"""DayContext schema."""

from typing import TYPE_CHECKING

from pydantic import Field

from .base import BaseSchema

if TYPE_CHECKING:
    from .brain_dump import BrainDumpSchema
    from .calendar_entry import CalendarEntrySchema
    from .day import DaySchema
    from .message import MessageSchema
    from .push_notification import PushNotificationSchema
    from .routine import RoutineSchema
    from .task import TaskSchema


class DayContextSchema(BaseSchema):
    """API schema for DayContext value object."""

    day: "DaySchema"
    calendar_entries: list["CalendarEntrySchema"] = Field(default_factory=list)
    tasks: list["TaskSchema"] = Field(default_factory=list)
    routines: list["RoutineSchema"] = Field(default_factory=list)
    brain_dumps: list["BrainDumpSchema"] = Field(default_factory=list)
    push_notifications: list["PushNotificationSchema"] = Field(default_factory=list)
    messages: list["MessageSchema"] = Field(default_factory=list)
