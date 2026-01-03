"""Query to preview tasks that would be created for a given date."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from loguru import logger
from planned.application.unit_of_work import UnitOfWorkFactory, UnitOfWorkProtocol
from planned.domain import value_objects
from planned.domain.entities import TaskEntity
from planned.domain.services.routine import RoutineService

from .base import Query, QueryHandler


@dataclass(frozen=True)
class PreviewTasksQuery(Query):
    """Query to preview tasks that would be created for a given date.

    Returns a list of tasks that would be created from active routines.
    These tasks are not saved to the database.
    """

    user_id: UUID
    date: date


class PreviewTasksHandler(QueryHandler[PreviewTasksQuery, list[TaskEntity]]):
    """Handles PreviewTasksQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, query: PreviewTasksQuery) -> list[TaskEntity]:
        """Preview tasks that would be created for a given date.

        Args:
            query: The preview tasks query

        Returns:
            List of tasks that would be created
        """
        async with self._uow_factory.create(query.user_id) as uow:
            return await self._preview_tasks(uow, query.user_id, query.date)

    async def _preview_tasks(
        self,
        uow: UnitOfWorkProtocol,
        user_id: UUID,
        target_date: date,
    ) -> list[TaskEntity]:
        """Generate preview tasks from routines."""
        result: list[TaskEntity] = []

        for routine in await uow.routines.all():
            logger.debug(f"Checking routine: {routine.name}")
            if RoutineService.is_routine_active(routine.routine_schedule, target_date):
                for routine_task in routine.tasks:
                    task_def = await uow.task_definitions.get(
                        routine_task.task_definition_id,
                    )
                    task = TaskEntity(
                        user_id=user_id,
                        name=routine_task.name or f"ROUTINE: {routine.name}",
                        frequency=routine.routine_schedule.frequency,
                        routine_id=routine.id,
                        task_definition=task_def,
                        schedule=routine_task.schedule,
                        scheduled_date=target_date,
                        status=value_objects.TaskStatus.NOT_STARTED,
                        category=routine.category,
                    )
                    result.append(task)

        return result
