"""Query to preview tasks that would be created for a given date."""

from dataclasses import dataclass
from datetime import date

from loguru import logger

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import (
    RoutineDefinitionRepositoryReadOnlyProtocol,
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

    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol
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

        for routine_definition in await self.routine_definition_ro_repo.all():
            logger.debug(f"Checking routine definition: {routine_definition.name}")
            if routine_definition.routine_definition_schedule.is_active_for_date(
                target_date
            ):
                for routine_definition_task in routine_definition.tasks:
                    # Check if task has its own schedule - if so, both routine definition and task schedules must match
                    if (
                        routine_definition_task.task_schedule is not None
                        and not routine_definition_task.task_schedule.is_active_for_date(
                            target_date
                        )
                    ):
                        logger.debug(
                            f"Skipping task {routine_definition_task.name} - task schedule doesn't match date",
                        )
                        continue

                    task_def = await self.task_definition_ro_repo.get(
                        routine_definition_task.task_definition_id,
                    )
                    task_time_window = (
                        routine_definition_task.time_window
                        or routine_definition.time_window
                    )
                    task = TaskEntity(
                        user_id=self.user_id,
                        name=(
                            routine_definition_task.name
                            or f"ROUTINE DEFINITION: {routine_definition.name}"
                        ),
                        frequency=routine_definition.routine_definition_schedule.frequency,
                        routine_definition_id=routine_definition.id,
                        type=task_def.type,
                        description=task_def.description,
                        time_window=task_time_window,
                        scheduled_date=target_date,
                        status=value_objects.TaskStatus.NOT_STARTED,
                        category=routine_definition.category,
                    )
                    result.append(task)

        return result
