"""Query to preview tasks that would be created for a given date."""

from datetime import date
from uuid import UUID

from loguru import logger
from planned.application.unit_of_work import ReadOnlyRepositories
from planned.domain import value_objects
from planned.domain.entities import TaskEntity
from planned.domain.services.routine import RoutineService


class PreviewTasksHandler:
    """Previews tasks that would be created for a given date."""

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        self._ro_repos = ro_repos
        self.user_id = user_id

    async def preview_tasks(self, date: date) -> list[TaskEntity]:
        """Preview tasks that would be created for a given date.

        Args:
            date: The date to preview tasks for

        Returns:
            List of tasks that would be created
        """
        result: list[TaskEntity] = []

        for routine in await self._ro_repos.routine_ro_repo.all():
            logger.debug(f"Checking routine: {routine.name}")
            if RoutineService.is_routine_active(routine.routine_schedule, date):
                for routine_task in routine.tasks:
                    task_def = await self._ro_repos.task_definition_ro_repo.get(
                        routine_task.task_definition_id,
                    )
                    task = TaskEntity(
                        user_id=self.user_id,
                        name=routine_task.name or f"ROUTINE: {routine.name}",
                        frequency=routine.routine_schedule.frequency,
                        routine_id=routine.id,
                        task_definition=task_def,
                        schedule=routine_task.schedule,
                        scheduled_date=date,
                        status=value_objects.TaskStatus.NOT_STARTED,
                        category=routine.category,
                    )
                    result.append(task)

        return result
