"""Protocol for MessageRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain.entities import MessageEntity


class MessageRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[MessageEntity]):
    """Read-only protocol defining the interface for message repositories."""


class MessageRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[MessageEntity]):
    """Read-write protocol defining the interface for message repositories."""

