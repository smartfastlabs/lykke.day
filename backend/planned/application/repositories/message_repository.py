"""Protocol for MessageRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain.entities import Message


class MessageRepositoryProtocol(DateScopedCrudRepositoryProtocol[Message]):
    """Protocol defining the interface for message repositories."""
    pass

