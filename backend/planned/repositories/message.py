from planned.objects import Message

from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    Object = Message
    _prefix = "messages"
