"""Command to schedule a day with tasks from routines."""

import asyncio
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from planned.application.queries.preview_day import PreviewDayHandler, PreviewDayQuery
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import value_objects
from planned.domain.entities import DayEntity

from .base import Command, CommandHandler


@dataclass(frozen=True)
class ScheduleDayCommand(Command):
    """Command to schedule a day with tasks from routines.

    Creates tasks based on active routines and marks the day as scheduled.
    """

    user_id: UUID
    date: date
    template_id: UUID | None = None


class ScheduleDayHandler(CommandHandler[ScheduleDayCommand, value_objects.DayContext]):
    """Handles ScheduleDayCommand."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._preview_handler = PreviewDayHandler(uow_factory)

    async def handle(self, cmd: ScheduleDayCommand) -> value_objects.DayContext:
        """Schedule a day with tasks from routines.

        Args:
            cmd: The schedule command

        Returns:
            A DayContext with the scheduled day and tasks
        """
        async with self._uow_factory.create(cmd.user_id) as uow:
            # Delete existing tasks for this date
            await uow.tasks.delete_many(value_objects.DateQuery(date=cmd.date))

            # Get preview of what the day would look like
            preview_query = PreviewDayQuery(
                user_id=cmd.user_id,
                date=cmd.date,
                template_id=cmd.template_id,
            )
            preview_result = await self._preview_handler.handle(preview_query)

            # Validate template exists
            if preview_result.day.template is None:
                raise ValueError("Day template is required to schedule")

            # Re-fetch template to ensure it's in the current UoW context
            template = await uow.day_templates.get(preview_result.day.template.id)

            # Create and schedule the day
            day = DayEntity.create_for_date(
                cmd.date,
                user_id=cmd.user_id,
                template=template,
            )
            day.schedule(template)

            # Get tasks from preview
            tasks = preview_result.tasks

            # Save day and tasks
            await asyncio.gather(
                uow.days.put(day),
                *[uow.tasks.put(task) for task in tasks],
            )
            await uow.commit()

            return value_objects.DayContext(
                day=day,
                tasks=tasks,
                calendar_entries=preview_result.calendar_entries,
                messages=preview_result.messages,
            )

