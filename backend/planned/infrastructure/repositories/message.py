from planned.domain.entities import Message

from .base import BaseDateRepository
from .base.schema import messages


class MessageRepository(BaseDateRepository[Message]):
    Object = Message
    table = messages
