"""Command to schedule a day with tasks from routines."""

import asyncio
from datetime import date as dt_date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.application.queries.preview_day import PreviewDayHandler
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


class ScheduleDayHandler(BaseCommandHandler):
    """Schedules a day with tasks from routines."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        preview_day_handler: PreviewDayHandler,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self.preview_day_handler = preview_day_handler

    async def schedule_day(
        self, date: dt_date, template_id: UUID | None = None
    ) -> value_objects.DayContext:
        """Schedule a day with tasks from routines.

        Args:
            date: The date to schedule
            template_id: Optional template ID to use

        Returns:
            A DayContext with the scheduled day and tasks
        """
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            try:
                existing_day = await uow.day_ro_repo.get(day_id)
                tasks, calendar_entries = await asyncio.gather(
                    uow.task_ro_repo.search(value_objects.TaskQuery(date=date)),
                    uow.calendar_entry_ro_repo.search(
                        value_objects.CalendarEntryQuery(date=date)
                    ),
                )
                return value_objects.DayContext(
                    day=existing_day,
                    tasks=tasks,
                    calendar_entries=calendar_entries,
                )
            except NotFoundError:
                # Delete existing tasks for this date (defensive cleanup)
                await uow.bulk_delete_tasks(value_objects.TaskQuery(date=date))

                # Get preview of what the day would look like
                preview_result = await self.preview_day_handler.preview_day(
                    date, template_id
                )

                # Validate template exists
                if preview_result.day.template is None:
                    raise ValueError("Day template is required to schedule")

                # Re-fetch template to ensure it's in the current UoW context
                template = await uow.day_template_ro_repo.get(
                    preview_result.day.template.id
                )

                # Convert template timeblocks to day timeblocks
                day_time_blocks: list[value_objects.DayTimeBlock] = []
                if template.time_blocks:
                    # Get unique time block definition IDs
                    unique_def_ids = {
                        tb.time_block_definition_id for tb in template.time_blocks
                    }
                    # Fetch all time block definitions
                    time_block_defs = await asyncio.gather(
                        *[
                            uow.time_block_definition_ro_repo.get(def_id)
                            for def_id in unique_def_ids
                        ]
                    )
                    # Create a lookup map
                    def_map = {def_.id: def_ for def_ in time_block_defs}

                    # Convert each template timeblock to a day timeblock
                    for template_tb in template.time_blocks:
                        time_block_def = def_map[template_tb.time_block_definition_id]
                        day_time_blocks.append(
                            value_objects.DayTimeBlock(
                                time_block_definition_id=template_tb.time_block_definition_id,
                                start_time=template_tb.start_time,
                                end_time=template_tb.end_time,
                                name=template_tb.name,
                                type=time_block_def.type,
                                category=time_block_def.category,
                            )
                        )

                # Create and schedule the day
                day = DayEntity.create_for_date(
                    date,
                    user_id=self.user_id,
                    template=template,
                )
                # Set timeblocks before scheduling
                day.time_blocks = day_time_blocks
                day.schedule(template)
                await uow.create(day)

                # Get tasks from preview and create them
                tasks = preview_result.tasks
                for task in tasks:
                    await uow.create(task)

                return value_objects.DayContext(
                    day=day,
                    tasks=tasks,
                    calendar_entries=preview_result.calendar_entries,
                )
