"""Protocol for MessageRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity


class MessageRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[MessageEntity]):
    """Read-only protocol defining the interface for message repositories."""

    Query = value_objects.MessageQuery


class MessageRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[MessageEntity]):
    """Read-write protocol defining the interface for message repositories."""

    Query = value_objects.MessageQuery
