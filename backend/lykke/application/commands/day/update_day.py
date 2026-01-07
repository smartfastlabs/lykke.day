"""Command to update a day's status or template."""

from datetime import date

from lykke.application.commands.base import BaseCommandHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity
from lykke.domain.value_objects import DayUpdateObject


class UpdateDayHandler(BaseCommandHandler):
    """Updates a day's status or template."""

    async def update_day(
        self,
        date: date,
        update_data: DayUpdateObject,
    ) -> DayEntity:
        """Update a day's status and/or template.

        Args:
            date: The date of the day to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            try:
                day = await uow.day_ro_repo.get(day_id)
            except NotFoundError:
                # Create a new day if it doesn't exist
                user = await uow.user_ro_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_ro_repo.get_by_slug(template_slug)
                day = DayEntity.create_for_date(
                    date, user_id=self.user_id, template=template
                )
                await uow.create(day)

            # Apply status transition if requested
            if update_data.status is not None:
                self._apply_status_transition(day, update_data.status)

            # Update template if requested
            if update_data.template_id is not None:
                template = await uow.day_template_ro_repo.get(update_data.template_id)
                day.update_template(template)

            # Update other fields if provided
            if update_data.alarm is not None:
                day.alarm = update_data.alarm
            if update_data.scheduled_at is not None:
                day.scheduled_at = update_data.scheduled_at
            if update_data.tags is not None:
                day.tags = update_data.tags

            # Add entity to UoW for saving
            uow.add(day)
            return day

    def _apply_status_transition(
        self, day: DayEntity, new_status: value_objects.DayStatus
    ) -> None:
        """Apply a status transition using domain methods.

        Args:
            day: The day to update
            new_status: The desired new status
        """
        if new_status == value_objects.DayStatus.SCHEDULED and day.template:
            day.schedule(day.template)
        elif new_status == value_objects.DayStatus.UNSCHEDULED:
            day.unschedule()
        elif new_status == value_objects.DayStatus.COMPLETE:
            day.complete()
        else:
            # For other statuses, set directly (maintains compatibility)
            day.status = new_status
