from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..entities.event import Event
    from ..entities.message import Message
    from ..entities.task import Task
    from ..entities.day import Day


class DayTag(str, Enum):
    WEEKEND = "WEEKEND"
    VACATION = "VACATION"
    WORKDAY = "WORKDAY"


class DayStatus(str, Enum):
    UNSCHEDULED = "UNSCHEDULED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


class DayMode(str, Enum):
    PRE_DAY = "PRE_DAY"
    LYKKE = "LYKKE"
    WORK = "WORK"
    POST_DAY = "POST_DAY"


class DayContext(BaseModel):
    day: "Day"
    events: list["Event"] = Field(default_factory=list)
    tasks: list["Task"] = Field(default_factory=list)
    messages: list["Message"] = Field(default_factory=list)


def _rebuild_day_context() -> None:
    """Rebuild DayContext model after all entity classes are defined."""
    # TODO: Move imports to top if circular import can be resolved
    # These imports are here to rebuild the model after all entities are defined
    from ..entities.day import Day  # noqa: F401
    from ..entities.event import Event  # noqa: F401
    from ..entities.message import Message  # noqa: F401
    from ..entities.task import Task  # noqa: F401
    
    DayContext.model_rebuild()

