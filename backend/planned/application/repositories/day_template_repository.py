"""Protocol for DayTemplateRepository."""

from typing import Protocol

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.domain.entities import DayEntity, DayTemplateEntity


class DayTemplateRepositoryProtocol(CrudRepositoryProtocol[DayTemplateEntity], Protocol):
    """Protocol defining the interface for day template repositories."""
    
    async def get_by_slug(self, slug: str) -> DayTemplateEntity:
        """Get a DayTemplate by slug (must be scoped to a user)."""
        ...

