"""Protocol for MessageRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain import entities


class MessageRepositoryProtocol(DateScopedCrudRepositoryProtocol[entities.Message]):
    """Protocol defining the interface for message repositories."""
    pass

