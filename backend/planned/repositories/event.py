from planned.objects import Event

from .base import BaseDateRepository


class EventRepository(BaseDateRepository[Event]):
    Object = Event
    _prefix = "events"
