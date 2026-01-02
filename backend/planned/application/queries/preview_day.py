"""Query to preview what a day would look like if scheduled."""

import asyncio
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from loguru import logger

from planned.application.unit_of_work import UnitOfWorkFactory, UnitOfWorkProtocol
from planned.core.exceptions import NotFoundError
from planned.domain import entities as objects
from planned.domain.entities import DayContext, DayTemplate, Task, TaskStatus
from planned.domain.value_objects.query import DateQuery

from .base import Query, QueryHandler


def _is_routine_active(schedule: objects.RoutineSchedule, target_date: date) -> bool:
    """Check if a routine is active for the given date."""
    if not schedule.weekdays:
        return True
    return target_date.weekday() in schedule.weekdays


@dataclass(frozen=True)
class PreviewDayQuery(Query):
    """Query to preview what a day would look like if scheduled.

    Returns a DayContext with preview data (not saved to database).
    Useful for showing users what tasks would be created.
    """

    user_id: UUID
    date: date
    template_id: UUID | None = None


class PreviewDayHandler(QueryHandler[PreviewDayQuery, DayContext]):
    """Handles PreviewDayQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, query: PreviewDayQuery) -> DayContext:
        """Preview what a day would look like if scheduled.

        Args:
            query: The query containing user_id, date, and optional template_id

        Returns:
            A DayContext with preview data (not saved)
        """
        async with self._uow_factory.create(query.user_id) as uow:
            # Get template
            template = await self._get_template(uow, query)

            # Create preview day
            day = objects.Day.create_for_date(
                query.date,
                user_id=query.user_id,
                template=template,
            )

            # Load preview tasks and existing data in parallel
            tasks, calendar_entries, messages = await asyncio.gather(
                self._preview_tasks(uow, query.user_id, query.date),
                uow.calendar_entries.search_query(DateQuery(date=query.date)),
                uow.messages.search_query(DateQuery(date=query.date)),
            )

            return DayContext(
                day=day,
                tasks=tasks,
                calendar_entries=calendar_entries,
                messages=messages,
            )

    async def _get_template(
        self,
        uow: UnitOfWorkProtocol,
        query: PreviewDayQuery,
    ) -> DayTemplate:
        """Get the template to use for the preview."""
        if query.template_id is not None:
            return await uow.day_templates.get(query.template_id)

        # Try to get from existing day
        try:
            day_id = objects.Day.id_from_date_and_user(query.date, query.user_id)
            existing_day = await uow.days.get(day_id)
            if existing_day.template:
                return existing_day.template
        except NotFoundError:
            pass

        # Fall back to user's default template
        user = await uow.users.get(query.user_id)
        template_slug = user.settings.template_defaults[query.date.weekday()]
        return await uow.day_templates.get_by_slug(template_slug)

    async def _preview_tasks(
        self,
        uow: UnitOfWorkProtocol,
        user_id: UUID,
        target_date: date,
    ) -> list[Task]:
        """Generate preview tasks from routines."""
        result: list[Task] = []

        for routine in await uow.routines.all():
            logger.debug(f"Checking routine: {routine.name}")
            if _is_routine_active(routine.routine_schedule, target_date):
                for routine_task in routine.tasks:
                    task_def = await uow.task_definitions.get(
                        routine_task.task_definition_id,
                    )
                    task = Task(
                        user_id=user_id,
                        name=routine_task.name or f"ROUTINE: {routine.name}",
                        frequency=routine.routine_schedule.frequency,
                        routine_id=routine.id,
                        task_definition=task_def,
                        schedule=routine_task.schedule,
                        scheduled_date=target_date,
                        status=TaskStatus.NOT_STARTED,
                        category=routine.category,
                    )
                    result.append(task)

        return result

