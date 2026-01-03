"""Protocol for TaskDefinitionRepository."""

from planned.application.repositories.base import SimpleReadRepositoryProtocol
from planned.domain.entities import TaskDefinitionEntity, TaskEntity


class TaskDefinitionRepositoryProtocol(SimpleReadRepositoryProtocol[TaskDefinitionEntity]):
    """Protocol defining the interface for task definition repositories."""
    pass

