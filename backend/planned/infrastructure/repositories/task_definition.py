from typing import Any
from uuid import UUID

from planned.domain.entities import TaskDefinition
from planned.infrastructure.database.tables import task_definitions_tbl

from .base import BaseQuery, UserScopedBaseRepository
from .base.utils import normalize_list_fields


class TaskDefinitionRepository(UserScopedBaseRepository[TaskDefinition, BaseQuery]):
    Object = TaskDefinition
    table = task_definitions_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize TaskDefinitionRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(task_definition: TaskDefinition) -> dict[str, Any]:
        """Convert a TaskDefinition entity to a database row dict."""
        row: dict[str, Any] = {
            "id": task_definition.id,
            "user_id": task_definition.user_id,
            "name": task_definition.name,
            "description": task_definition.description,
            "type": task_definition.type.value,
        }

        return row

    @staticmethod
    def row_to_entity(row: dict[str, Any]) -> TaskDefinition:
        """Convert a database row dict to a TaskDefinition entity."""
        # Normalize None values to [] for list-typed fields
        data = normalize_list_fields(row, TaskDefinition)
        return TaskDefinition.model_validate(data, from_attributes=True)
