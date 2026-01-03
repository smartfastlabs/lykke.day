"""Command to unschedule a day, removing routine tasks."""

import asyncio
from datetime import date
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import DayEntity


class UnscheduleDayHandler:
    """Unschedules a day, removing routine tasks."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def unschedule_day(self, user_id: UUID, date: date) -> DayEntity:
        """Unschedule a day, removing routine tasks and marking day as unscheduled.

        Args:
            user_id: The user ID
            date: The date to unschedule

        Returns:
            The updated Day entity
        """
        async with self._uow_factory.create(user_id) as uow:
            # Get all tasks for the date, filter for routine tasks, then delete them
            tasks = await uow.task_rw_repo.search_query(value_objects.DateQuery(date=date))
            routine_tasks = [t for t in tasks if t.routine_id is not None]
            if routine_tasks:
                await asyncio.gather(
                    *[uow.task_rw_repo.delete(task) for task in routine_tasks]
                )

            # Get or create the day
            day_id = DayEntity.id_from_date_and_user(date, user_id)
            try:
                day = await uow.day_rw_repo.get(day_id)
            except NotFoundError:
                # Day doesn't exist, create it
                user = await uow.user_rw_repo.get(user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_rw_repo.get_by_slug(template_slug)
                day = DayEntity.create_for_date(
                    date, user_id=user_id, template=template
                )

            # Unschedule the day using domain method
            day.unschedule()
            await uow.day_rw_repo.put(day)
            await uow.commit()
            return day

