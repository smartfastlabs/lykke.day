"""Command to schedule a day with tasks from routines."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, time as dt_time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.queries.preview_day import PreviewDayHandler
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    UnitOfWorkFactory,
    UnitOfWorkProtocol,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity, DayEntity, DayTemplateEntity, TaskEntity
from lykke.domain.events.day_events import DayUpdatedEvent


@dataclass(frozen=True)
class ScheduleDayCommand(Command):
    """Command to schedule a day."""

    date: dt_date
    template_id: UUID | None = None


class ScheduleDayHandler(BaseCommandHandler[ScheduleDayCommand, value_objects.DayContext]):
    """Schedules a day with tasks from routines."""

    @staticmethod
    def _time_to_local_datetime(
        date: dt_date,
        time_value: dt_time,
        *,
        timezone: ZoneInfo,
        template_start: dt_time | None,
        template_crosses_midnight: bool,
    ) -> datetime:
        dt_value = datetime.combine(date, time_value, tzinfo=timezone)
        if (
            template_crosses_midnight
            and template_start is not None
            and time_value < template_start
        ):
            dt_value += timedelta(days=1)
        return dt_value

    @classmethod
    def _calculate_day_bounds(
        cls,
        *,
        date: dt_date,
        template: DayTemplateEntity,
        tasks: list[TaskEntity],
        calendar_entries: list[CalendarEntryEntity],
        timezone: ZoneInfo,
    ) -> tuple[datetime | None, datetime | None]:
        buffer = timedelta(minutes=30)

        template_start = template.start_time
        template_end = template.end_time
        template_crosses_midnight = bool(
            template_start and template_end and template_end < template_start
        )

        template_start_dt = (
            cls._time_to_local_datetime(
                date,
                template_start,
                timezone=timezone,
                template_start=template_start,
                template_crosses_midnight=template_crosses_midnight,
            )
            if template_start
            else None
        )
        template_end_dt = (
            cls._time_to_local_datetime(
                date,
                template_end,
                timezone=timezone,
                template_start=template_start,
                template_crosses_midnight=template_crosses_midnight,
            )
            if template_end
            else None
        )

        if (
            template_start_dt is not None
            and template_end_dt is not None
            and template_end_dt < template_start_dt
        ):
            template_end_dt += timedelta(days=1)

        day_start_dt = template_start_dt
        day_end_dt = template_end_dt

        def consider_start(candidate: datetime | None) -> None:
            nonlocal day_start_dt
            if candidate is None:
                return
            if template_start_dt is None or candidate < template_start_dt:
                candidate = candidate - buffer
                if day_start_dt is None or candidate < day_start_dt:
                    day_start_dt = candidate

        def consider_end(candidate: datetime | None) -> None:
            nonlocal day_end_dt
            if candidate is None:
                return
            if template_end_dt is None or candidate > template_end_dt:
                candidate = candidate + buffer
                if day_end_dt is None or candidate > day_end_dt:
                    day_end_dt = candidate

        for task in tasks:
            schedule = task.schedule
            if not schedule:
                continue

            start_dt = None
            end_dt = None
            if schedule.start_time is not None:
                start_dt = cls._time_to_local_datetime(
                    date,
                    schedule.start_time,
                    timezone=timezone,
                    template_start=template_start,
                    template_crosses_midnight=template_crosses_midnight,
                )
            if schedule.end_time is not None:
                end_dt = cls._time_to_local_datetime(
                    date,
                    schedule.end_time,
                    timezone=timezone,
                    template_start=template_start,
                    template_crosses_midnight=template_crosses_midnight,
                )

            if start_dt is not None and end_dt is not None and end_dt < start_dt:
                end_dt += timedelta(days=1)

            consider_start(start_dt)
            consider_end(end_dt)
            if end_dt is None and start_dt is not None:
                consider_end(start_dt)

        for entry in calendar_entries:
            start_local = entry.starts_at.astimezone(timezone)
            consider_start(start_local)
            if entry.ends_at:
                end_local = entry.ends_at.astimezone(timezone)
                consider_end(end_local)
            else:
                consider_end(start_local)

        start_utc = day_start_dt.astimezone(UTC) if day_start_dt else None
        end_utc = day_end_dt.astimezone(UTC) if day_end_dt else None
        return start_utc, end_utc

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        preview_day_handler: PreviewDayHandler,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self.preview_day_handler = preview_day_handler

    async def handle(self, command: ScheduleDayCommand) -> value_objects.DayContext:
        """Schedule a day with tasks from routines.

        Args:
            command: The command containing the date and optional template ID

        Returns:
            A DayContext with the scheduled day and tasks
        """
        async with self.new_uow() as uow:
            return await self.schedule_day_in_uow(uow, command)

    async def schedule_day_in_uow(
        self,
        uow: UnitOfWorkProtocol,
        command: ScheduleDayCommand,
        *,
        existing_day: DayEntity | None = None,
        force: bool = False,
        cleanup_existing_tasks: bool = True,
    ) -> value_objects.DayContext:
        """Schedule a day using an existing unit of work.

        Args:
            uow: Unit of work to use for persistence
            command: The command containing the date and optional template ID
            existing_day: Existing day entity to update instead of creating a new one
            force: If True, bypass the early return for existing days
            cleanup_existing_tasks: If True, delete tasks for the date before scheduling
        """
        day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
        if existing_day is None:
            if force:
                try:
                    existing_day = await uow.day_ro_repo.get(day_id)
                except NotFoundError:
                    existing_day = None
            else:
                try:
                    existing_day = await uow.day_ro_repo.get(day_id)
                    tasks, calendar_entries = await asyncio.gather(
                        uow.task_ro_repo.search(value_objects.TaskQuery(date=command.date)),
                        uow.calendar_entry_ro_repo.search(
                            value_objects.CalendarEntryQuery(date=command.date)
                        ),
                    )
                    return value_objects.DayContext(
                        day=existing_day,
                        tasks=tasks,
                        calendar_entries=calendar_entries,
                    )
                except NotFoundError:
                    existing_day = None

        if cleanup_existing_tasks:
            # Delete existing tasks for this date (defensive cleanup)
            await uow.bulk_delete_tasks(value_objects.TaskQuery(date=command.date))

        # Get preview of what the day would look like
        preview_result = await self.preview_day_handler.preview_day(
            command.date, command.template_id
        )

        # Validate template exists
        if preview_result.day.template is None:
            raise ValueError("Day template is required to schedule")

        # Re-fetch template to ensure it's in the current UoW context
        template = await uow.day_template_ro_repo.get(preview_result.day.template.id)

        timezone = ZoneInfo("UTC")
        user_repo = getattr(uow, "user_ro_repo", None) or self.user_ro_repo
        try:
            user = await user_repo.get(self.user_id)
        except Exception:
            user = None
        if user and user.settings.timezone:
            try:
                timezone = ZoneInfo(user.settings.timezone)
            except (ZoneInfoNotFoundError, ValueError):
                timezone = ZoneInfo("UTC")

        starts_at, ends_at = self._calculate_day_bounds(
            date=command.date,
            template=template,
            tasks=preview_result.tasks,
            calendar_entries=preview_result.calendar_entries,
            timezone=timezone,
        )

        # Convert template timeblocks to day timeblocks
        day_time_blocks: list[value_objects.DayTimeBlock] = []
        if template.time_blocks:
            # Get unique time block definition IDs
            unique_def_ids = {tb.time_block_definition_id for tb in template.time_blocks}
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

        if existing_day is None:
            # Create and schedule the day
            day = DayEntity.create_for_date(
                command.date,
                user_id=self.user_id,
                template=template,
            )
            day.high_level_plan = template.high_level_plan
            day.starts_at = starts_at
            day.ends_at = ends_at
            # Set timeblocks before scheduling
            day.time_blocks = day_time_blocks
            day.schedule(template)
            await uow.create(day)
        else:
            day = existing_day
            day.update_template(template)
            day.time_blocks = day_time_blocks
            day.starts_at = starts_at
            day.ends_at = ends_at
            if day.high_level_plan is None and template.high_level_plan is not None:
                day.high_level_plan = template.high_level_plan
            if day.status == value_objects.DayStatus.UNSCHEDULED:
                day.schedule(template)
            if not day.has_events():
                day.add_event(
                    DayUpdatedEvent(
                        update_object=value_objects.DayUpdateObject(
                            template_id=template.id,
                            time_blocks=day_time_blocks,
                            starts_at=starts_at,
                            ends_at=ends_at,
                        )
                    )
                )
            uow.add(day)

        # Get tasks from preview and create them
        tasks = preview_result.tasks
        for task in tasks:
            await uow.create(task)

        return value_objects.DayContext(
            day=day,
            tasks=tasks,
            calendar_entries=preview_result.calendar_entries,
        )
