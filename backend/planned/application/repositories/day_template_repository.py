"""Protocol for DayTemplateRepository."""

from planned.application.repositories.base import SimpleReadRepositoryProtocol
from planned.domain.entities import DayTemplate


class DayTemplateRepositoryProtocol(SimpleReadRepositoryProtocol[DayTemplate]):
    """Protocol defining the interface for day template repositories."""
    pass

