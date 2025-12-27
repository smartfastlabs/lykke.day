from planned.domain.entities import Event

from .base import BaseDateRepository
from .base.schema import events


class EventRepository(BaseDateRepository[Event]):
    Object = Event
    table = events
