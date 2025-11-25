from planned.objects import Event

from .base import BaseRepository


class EventRepository(BaseRepository[Event]):
    Object = Event
    _prefix = "events"
