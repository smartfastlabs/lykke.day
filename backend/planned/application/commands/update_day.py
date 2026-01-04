"""Command to update a day's status or template."""

from datetime import date
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import DayEntity
from planned.domain.value_objects import DayUpdateObject


class UpdateDayHandler:
    """Updates a day's status or template."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def update_day(
        self,
        user_id: UUID,
        date: date,
        update_data: DayUpdateObject,
    ) -> DayEntity:
        """Update a day's status and/or template.

        Args:
            user_id: The user ID
            date: The date of the day to update
            update_data: The update data containing optional fields to update

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self._uow_factory.create(user_id) as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(date, user_id)
            try:
                day = await uow.day_rw_repo.get(day_id)
            except NotFoundError:
                # Create a new day if it doesn't exist
                user = await uow.user_rw_repo.get(user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_rw_repo.get_by_slug(template_slug)
                day = DayEntity.create_for_date(date, user_id=user_id, template=template)

            # Apply status transition if requested
            if update_data.status is not None:
                self._apply_status_transition(day, update_data.status)

            # Update template if requested
            if update_data.template_id is not None:
                template = await uow.day_template_rw_repo.get(update_data.template_id)
                day.update_template(template)

            # Update other fields if provided
            if update_data.alarm is not None:
                day.alarm = update_data.alarm
            if update_data.scheduled_at is not None:
                day.scheduled_at = update_data.scheduled_at
            if update_data.tags is not None:
                day.tags = update_data.tags

            # Save and commit
            await uow.day_rw_repo.put(day)
            await uow.commit()
            return day

    def _apply_status_transition(self, day: DayEntity, new_status: value_objects.DayStatus) -> None:
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

