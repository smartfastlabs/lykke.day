"""SQLAlchemy implementation of TimeBlockDefinitionRepository."""

from typing import Any
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

    @staticmethod
    def entity_to_row(time_block_definition: TimeBlockDefinition) -> dict[str, Any]:
        """Convert a TimeBlockDefinition entity to a database row dict."""
        row: dict[str, Any] = {
            "id": time_block_definition.id,
            "user_id": time_block_definition.user_id,
            "name": time_block_definition.name,
            "description": time_block_definition.description,
            "type": time_block_definition.type.value,
            "category": time_block_definition.category.value,
        }
        return row

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> TimeBlockDefinition:
        """Convert a database row dict to a TimeBlockDefinition entity.

        Overrides base to handle enum conversion for type and category fields.
        """
        data = dict(row)

        # Convert string values to enums
        if "type" in data and isinstance(data["type"], str):
            data["type"] = value_objects.TimeBlockType(data["type"])
        if "category" in data and isinstance(data["category"], str):
            data["category"] = value_objects.TimeBlockCategory(data["category"])

        return cls.Object(**data)

