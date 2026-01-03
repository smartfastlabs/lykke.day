"""DayContext schema."""

from typing import TYPE_CHECKING

from pydantic import Field

from .base import BaseSchema

if TYPE_CHECKING:
    from .calendar_entry import CalendarEntry
    from .day import Day
    from .message import Message
    from .task import Task


class DayContext(BaseSchema):
    """API schema for DayContext value object."""

    day: "Day"
    calendar_entries: list["CalendarEntry"] = Field(default_factory=list)
    tasks: list["Task"] = Field(default_factory=list)
    messages: list["Message"] = Field(default_factory=list)

