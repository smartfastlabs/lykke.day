"""DayContext schema."""

from typing import TYPE_CHECKING

from pydantic import Field

from .base import BaseSchema

if TYPE_CHECKING:
    from .calendar_entry import CalendarEntrySchema
    from .day import DaySchema
    from .message import MessageSchema
    from .task import TaskSchema


class DayContextSchema(BaseSchema):
    """API schema for DayContext value object."""

    day: "DaySchema"
    calendar_entries: list["CalendarEntrySchema"] = Field(default_factory=list)
    tasks: list["TaskSchema"] = Field(default_factory=list)
    messages: list["MessageSchema"] = Field(default_factory=list)

