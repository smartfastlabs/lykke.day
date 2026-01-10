"""SQLAlchemy implementation of TimeBlockDefinitionRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lykke.application.repositories.time_block_definition_repository import (
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
    TimeBlockDefinitionRepositoryReadWriteProtocol,
)
from lykke.domain import value_objects
from lykke.domain.data_objects import TimeBlockDefinition
from lykke.infrastructure.database import tables

from .base import ReadOnlyRepository, ReadWriteRepository


class TimeBlockDefinitionReadOnlyRepository(
    ReadOnlyRepository[TimeBlockDefinition],
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
):
    """Read-only repository for TimeBlockDefinition entities."""

    Query = value_objects.TimeBlockDefinitionQuery

    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        """Initialize the repository with a database session and user_id."""
        super().__init__(
            session=session,
            user_id=user_id,
            table=tables.TimeBlockDefinition,
            entity_class=TimeBlockDefinition,
        )


class TimeBlockDefinitionReadWriteRepository(
    ReadWriteRepository[TimeBlockDefinition],
    TimeBlockDefinitionRepositoryReadWriteProtocol,
):
    """Read-write repository for TimeBlockDefinition entities."""

    Query = value_objects.TimeBlockDefinitionQuery

    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        """Initialize the repository with a database session and user_id."""
        super().__init__(
            session=session,
            user_id=user_id,
            table=tables.TimeBlockDefinition,
            entity_class=TimeBlockDefinition,
        )

