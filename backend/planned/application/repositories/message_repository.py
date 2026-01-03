"""Protocol for MessageRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain.entities import MessageEntity


class MessageRepositoryProtocol(DateScopedCrudRepositoryProtocol[MessageEntity]):
    """Protocol defining the interface for message repositories."""
    pass

