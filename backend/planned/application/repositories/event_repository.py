"""Protocol for EventRepository."""

from planned.application.repositories.base import DateScopedCrudRepositoryProtocol
from planned.domain.entities import Event


class EventRepositoryProtocol(DateScopedCrudRepositoryProtocol[Event]):
    """Protocol defining the interface for event repositories."""
    pass

