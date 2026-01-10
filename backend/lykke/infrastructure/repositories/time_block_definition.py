"""SQLAlchemy implementation of TimeBlockDefinitionRepository."""

from uuid import UUID

from lykke.domain import value_objects
from lykke.domain.data_objects import TimeBlockDefinition
from lykke.infrastructure.database.tables import time_block_definitions_tbl

from .base import BaseQuery, UserScopedBaseRepository


class TimeBlockDefinitionRepository(
    UserScopedBaseRepository[TimeBlockDefinition, BaseQuery]
):
    """Repository for TimeBlockDefinition data objects."""

    Object = TimeBlockDefinition
    table = time_block_definitions_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize TimeBlockDefinitionRepository with user scoping."""
        super().__init__(user_id=user_id)

