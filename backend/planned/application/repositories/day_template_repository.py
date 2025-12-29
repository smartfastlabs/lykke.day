"""Protocol for DayTemplateRepository."""

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.domain.entities import DayTemplate


class DayTemplateRepositoryProtocol(CrudRepositoryProtocol[DayTemplate]):
    """Protocol defining the interface for day template repositories."""
    pass

