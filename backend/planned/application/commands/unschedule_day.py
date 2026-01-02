"""Command to unschedule a day, removing routine tasks."""

import asyncio
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain import entities, value_objects

from .base import Command, CommandHandler


@dataclass(frozen=True)
class UnscheduleDayCommand(Command):
    """Command to unschedule a day, removing routine tasks and marking day as unscheduled."""

    user_id: UUID
    date: date


class UnscheduleDayHandler(CommandHandler[UnscheduleDayCommand, entities.Day]):
    """Handles UnscheduleDayCommand."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, cmd: UnscheduleDayCommand) -> entities.Day:
        """Unschedule a day, removing routine tasks and marking day as unscheduled.

        Args:
            cmd: The unschedule command

        Returns:
            The updated Day entity
        """
        async with self._uow_factory.create(cmd.user_id) as uow:
            # Get all tasks for the date, filter for routine tasks, then delete them
            tasks = await uow.tasks.search_query(value_objects.DateQuery(date=cmd.date))
            routine_tasks = [t for t in tasks if t.routine_id is not None]
            if routine_tasks:
                await asyncio.gather(
                    *[uow.tasks.delete(task) for task in routine_tasks]
                )

            # Get or create the day
            day_id = entities.Day.id_from_date_and_user(cmd.date, cmd.user_id)
            try:
                day = await uow.days.get(day_id)
            except NotFoundError:
                # Day doesn't exist, create it
                user = await uow.users.get(cmd.user_id)
                template_slug = user.settings.template_defaults[cmd.date.weekday()]
                template = await uow.day_templates.get_by_slug(template_slug)
                day = entities.Day.create_for_date(
                    cmd.date, user_id=cmd.user_id, template=template
                )

            # Unschedule the day using domain method
            day.unschedule()
            await uow.days.put(day)
            await uow.commit()
            return day

