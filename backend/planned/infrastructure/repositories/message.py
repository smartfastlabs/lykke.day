from planned.domain.entities import Message

from .base import BaseDateRepository


class MessageRepository(BaseDateRepository[Message]):
    Object = Message
    _prefix = "messages"
