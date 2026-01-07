"""Protocol for DayTemplateRepository."""

from typing import Protocol

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity


class DayTemplateRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[DayTemplateEntity], Protocol):
    """Read-only protocol defining the interface for day template repositories."""
    
    Query: type[value_objects.DayTemplateQuery] = value_objects.DayTemplateQuery
    
    async def get_by_slug(self, slug: str) -> DayTemplateEntity:
        """Get a DayTemplate by slug (must be scoped to a user)."""
        ...


class DayTemplateRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[DayTemplateEntity], Protocol):
    """Read-write protocol defining the interface for day template repositories."""
    
    Query: type[value_objects.DayTemplateQuery] = value_objects.DayTemplateQuery
    
    async def get_by_slug(self, slug: str) -> DayTemplateEntity:
        """Get a DayTemplate by slug (must be scoped to a user)."""
        ...

