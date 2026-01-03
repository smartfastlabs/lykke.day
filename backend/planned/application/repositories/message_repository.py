"""Protocol for MessageRepository."""

from planned.application.repositories.base import (
    DateScopedCrudRepositoryProtocol,
    ReadOnlyDateScopedRepositoryProtocol,
)
from planned.domain.entities import MessageEntity


class MessageRepositoryReadOnlyProtocol(ReadOnlyDateScopedRepositoryProtocol[MessageEntity]):
    """Read-only protocol defining the interface for message repositories."""
    pass


class MessageRepositoryReadWriteProtocol(DateScopedCrudRepositoryProtocol[MessageEntity]):
    """Read-write protocol defining the interface for message repositories."""
    pass

