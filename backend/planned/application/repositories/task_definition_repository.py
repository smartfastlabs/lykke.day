"""Protocol for TaskDefinitionRepository."""

from planned.application.repositories.base import SimpleReadRepositoryProtocol
from planned.domain import entities


class TaskDefinitionRepositoryProtocol(SimpleReadRepositoryProtocol[entities.TaskDefinition]):
    """Protocol defining the interface for task definition repositories."""
    pass

