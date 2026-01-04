"""Protocol for DayTemplateRepository."""

from typing import Protocol

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain import value_objects
from planned.domain.entities import DayTemplateEntity


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

