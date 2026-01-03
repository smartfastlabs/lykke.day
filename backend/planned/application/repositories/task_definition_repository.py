"""Protocol for TaskDefinitionRepository."""

from planned.application.repositories.base import CrudRepositoryProtocol
from planned.domain.entities import TaskDefinitionEntity


class TaskDefinitionRepositoryProtocol(CrudRepositoryProtocol[TaskDefinitionEntity]):
    """Protocol defining the interface for task definition repositories."""
    pass

