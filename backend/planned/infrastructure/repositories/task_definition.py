from typing import Any

from planned.domain.entities import TaskDefinition

from .base import BaseConfigRepository
from .base.schema import task_definitions


class TaskDefinitionRepository(BaseConfigRepository[TaskDefinition]):
    Object = TaskDefinition
    table = task_definitions

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
        return TaskDefinition.model_validate(row, from_attributes=True)
