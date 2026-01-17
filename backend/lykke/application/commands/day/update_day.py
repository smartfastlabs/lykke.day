"""Command to update a day's status or template."""

from dataclasses import dataclass
from datetime import date

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity
from lykke.domain.events.day_events import DayUpdatedEvent
from lykke.domain.value_objects import DayUpdateObject


@dataclass(frozen=True)
class UpdateDayCommand(Command):
    """Command to update a day."""

    date: date
    update_data: DayUpdateObject


class UpdateDayHandler(BaseCommandHandler[UpdateDayCommand, DayEntity]):
    """Updates a day's status or template."""

    async def handle(self, command: UpdateDayCommand) -> DayEntity:
        """Update a day's status and/or template.

        Args:
            command: The command containing the date and update data

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            update_data = command.update_data
            # Apply status transition if requested
            if update_data.status is not None:
                self._apply_status_transition(day, update_data.status)

            # Update template if requested
            if update_data.template_id is not None:
                template = await uow.day_template_ro_repo.get(update_data.template_id)
                day.update_template(template)

            # Update other fields if provided
            if update_data.scheduled_at is not None:
                day.scheduled_at = update_data.scheduled_at
            if update_data.tags is not None:
                day.tags = update_data.tags

            # Ensure at least one domain event is emitted for persistence
            if not day.has_events() and any(
                field is not None
                for field in (
                    update_data.status,
                    update_data.template_id,
                    update_data.scheduled_at,
                    update_data.tags,
                )
            ):
                day.add_event(DayUpdatedEvent(update_object=update_data))

            # Add entity to UoW for saving
            return uow.add(day)

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
