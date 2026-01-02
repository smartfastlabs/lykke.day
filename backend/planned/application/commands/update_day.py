"""Command to update a day's status or template."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain.entities import Day
from planned.domain.value_objects.day import DayStatus

from .base import Command, CommandHandler


@dataclass(frozen=True)
class UpdateDayCommand(Command):
    """Command to update a day's status and/or template.

    Applies status transitions using domain methods to ensure
    business rules are enforced.
    """

    user_id: UUID
    date: date
    status: DayStatus | None = None
    template_id: UUID | None = None


class UpdateDayHandler(CommandHandler[UpdateDayCommand, Day]):
    """Handles UpdateDayCommand."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, cmd: UpdateDayCommand) -> Day:
        """Update a day's status and/or template.

        Args:
            cmd: The update command

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self._uow_factory.create(cmd.user_id) as uow:
            # Get the existing day
            day_id = Day.id_from_date_and_user(cmd.date, cmd.user_id)
            try:
                day = await uow.days.get(day_id)
            except NotFoundError:
                # Create a new day if it doesn't exist
                user = await uow.users.get(cmd.user_id)
                template_slug = user.settings.template_defaults[cmd.date.weekday()]
                template = await uow.day_templates.get_by_slug(template_slug)
                day = Day.create_for_date(cmd.date, user_id=cmd.user_id, template=template)

            # Apply status transition if requested
            if cmd.status is not None:
                self._apply_status_transition(day, cmd.status)

            # Update template if requested
            if cmd.template_id is not None:
                template = await uow.day_templates.get(cmd.template_id)
                day.update_template(template)

            # Save and commit
            await uow.days.put(day)
            await uow.commit()
            return day

    def _apply_status_transition(self, day: Day, new_status: DayStatus) -> None:
        """Apply a status transition using domain methods.

        Args:
            day: The day to update
            new_status: The desired new status
        """
        if new_status == DayStatus.SCHEDULED and day.template:
            day.schedule(day.template)
        elif new_status == DayStatus.UNSCHEDULED:
            day.unschedule()
        elif new_status == DayStatus.COMPLETE:
            day.complete()
        else:
            # For other statuses, set directly (maintains compatibility)
            day.status = new_status

