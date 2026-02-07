"""Command to update a day's status or template."""

from dataclasses import dataclass, replace
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import (
    DayRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity
from lykke.domain.events.day_events import DayUpdatedEvent
from lykke.domain.value_objects import DayUpdateObject


@dataclass(frozen=True)
class UpdateDayCommand(Command):
    """Command to update a day."""

    day_id: UUID
    update_data: DayUpdateObject


class UpdateDayHandler(BaseCommandHandler[UpdateDayCommand, DayEntity]):
    """Updates a day's status or template."""

    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol

    async def handle(self, command: UpdateDayCommand) -> DayEntity:
        """Update a day's status and/or template.

        Args:
            command: The command containing the day id and update data

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day = await self.day_ro_repo.get(command.day_id)

            update_data = command.update_data
            if (
                update_data.status is None
                and update_data.high_level_plan is not None
                and day.status == value_objects.DayStatus.SCHEDULED
            ):
                update_data = replace(update_data, status=value_objects.DayStatus.STARTED)

            # Apply status transition if requested
            if update_data.status is not None:
                self._apply_status_transition(day, update_data.status)

            # Update template if requested
            if update_data.template_id is not None:
                template = await self.day_template_ro_repo.get(update_data.template_id)
                day.update_template(template)

            # Update other fields if provided
            if update_data.scheduled_at is not None:
                day.scheduled_at = update_data.scheduled_at
            if update_data.starts_at is not None:
                day.starts_at = update_data.starts_at
            if update_data.ends_at is not None:
                day.ends_at = update_data.ends_at
            if update_data.tags is not None:
                day.tags = update_data.tags
            if update_data.high_level_plan is not None:
                day.high_level_plan = update_data.high_level_plan

            has_updates = any(
                field is not None
                for field in (
                    update_data.status,
                    update_data.template_id,
                    update_data.scheduled_at,
                    update_data.starts_at,
                    update_data.ends_at,
                    update_data.tags,
                    update_data.high_level_plan,
                )
            )
            if has_updates and not day.has_events():
                day.add_event(
                    DayUpdatedEvent(update_object=update_data, user_id=day.user_id)
                )

            if has_updates:
                return uow.add(day)

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
