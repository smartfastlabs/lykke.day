"""Protocol for TaskDefinitionRepository."""

from planned.application.repositories.base import SimpleReadRepositoryProtocol
from planned.domain.entities import TaskDefinition


class TaskDefinitionRepositoryProtocol(SimpleReadRepositoryProtocol[TaskDefinition]):
    """Protocol defining the interface for task definition repositories."""
    pass

