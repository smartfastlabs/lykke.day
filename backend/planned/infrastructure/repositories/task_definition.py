from typing import Any
from uuid import UUID

from planned.domain.entities import TaskDefinitionEntity
from planned.infrastructure.database.tables import task_definitions_tbl

from .base import BaseQuery, UserScopedBaseRepository


class TaskDefinitionRepository(
    UserScopedBaseRepository[TaskDefinitionEntity, BaseQuery]
):
    Object = TaskDefinitionEntity
    table = task_definitions_tbl
    QueryClass = BaseQuery

    def __init__(self, user_id: UUID) -> None:
        """Initialize TaskDefinitionRepository with user scoping."""
        super().__init__(user_id=user_id)

    @staticmethod
    def entity_to_row(task_definition: TaskDefinitionEntity) -> dict[str, Any]:
        """Convert a TaskDefinition entity to a database row dict."""
        row: dict[str, Any] = {
            "id": task_definition.id,
            "user_id": task_definition.user_id,
            "name": task_definition.name,
            "description": task_definition.description,
            "type": task_definition.type,
        }

        return row
