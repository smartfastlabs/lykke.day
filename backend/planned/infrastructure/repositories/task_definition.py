from typing import Any

from planned.domain.entities import TaskDefinition

from .base import BaseQuery, BaseRepository
from .base.schema import task_definitions
from .base.utils import normalize_list_fields


class TaskDefinitionRepository(BaseRepository[TaskDefinition, BaseQuery]):
    Object = TaskDefinition
    table = task_definitions
    QueryClass = BaseQuery

    @staticmethod
    def entity_to_row(task_definition: TaskDefinition) -> dict[str, Any]:
        """Convert a TaskDefinition entity to a database row dict."""
        row: dict[str, Any] = {
            "id": task_definition.id,
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
