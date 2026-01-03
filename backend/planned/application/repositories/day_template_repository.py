"""Protocol for DayTemplateRepository."""

from typing import Protocol

from planned.application.repositories.base import (
    CrudRepositoryProtocol,
    ReadOnlyCrudRepositoryProtocol,
)
from planned.domain.entities import DayTemplateEntity


class DayTemplateRepositoryReadOnlyProtocol(ReadOnlyCrudRepositoryProtocol[DayTemplateEntity], Protocol):
    """Read-only protocol defining the interface for day template repositories."""
    
    async def get_by_slug(self, slug: str) -> DayTemplateEntity:
        """Get a DayTemplate by slug (must be scoped to a user)."""
        ...


class DayTemplateRepositoryReadWriteProtocol(CrudRepositoryProtocol[DayTemplateEntity], Protocol):
    """Read-write protocol defining the interface for day template repositories."""
    
    async def get_by_slug(self, slug: str) -> DayTemplateEntity:
        """Get a DayTemplate by slug (must be scoped to a user)."""
        ...

