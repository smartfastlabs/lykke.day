"""Query to preview tasks that would be created for a given date."""

from dataclasses import dataclass
from datetime import date

from loguru import logger
from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import (
    RoutineRepositoryReadOnlyProtocol,
    TaskDefinitionRepositoryReadOnlyProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import TaskEntity


@dataclass(frozen=True)
class PreviewTasksQuery(Query):
    """Query to preview tasks for a date."""

    date: date


class PreviewTasksHandler(BaseQueryHandler[PreviewTasksQuery, list[TaskEntity]]):
    """Previews tasks that would be created for a given date."""

    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol

    async def handle(self, query: PreviewTasksQuery) -> list[TaskEntity]:
        """Handle preview tasks query."""
        return await self.preview_tasks(query.date)

    async def preview_tasks(self, target_date: date) -> list[TaskEntity]:
        """Preview tasks that would be created for a given date.

        Args:
            target_date: The date to preview tasks for

        Returns:
            List of tasks that would be created
        """
        result: list[TaskEntity] = []

        for routine in await self.routine_ro_repo.all():
            logger.debug(f"Checking routine: {routine.name}")
            if routine.routine_schedule.is_active_for_date(target_date):
                for routine_task in routine.tasks:
                    # Check if task has its own schedule - if so, both routine and task schedules must match
                    if routine_task.task_schedule is not None:
                        if not routine_task.task_schedule.is_active_for_date(target_date):
                            logger.debug(
                                f"Skipping task {routine_task.name} - task schedule doesn't match date"
                            )
                            continue
                    
                    task_def = await self.task_definition_ro_repo.get(
                        routine_task.task_definition_id,
                    )
                    task = TaskEntity(
                        user_id=self.user_id,
                        name=routine_task.name or f"ROUTINE: {routine.name}",
                        frequency=routine.routine_schedule.frequency,
                        routine_id=routine.id,
                        type=task_def.type,
                        description=task_def.description,
                        schedule=routine_task.schedule,
                        scheduled_date=target_date,
                        status=value_objects.TaskStatus.NOT_STARTED,
                        category=routine.category,
                    )
                    result.append(task)

        return result
