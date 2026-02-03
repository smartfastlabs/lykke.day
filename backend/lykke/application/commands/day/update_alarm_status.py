"""Command to update an alarm's status on a day."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.utils.dates import ensure_utc
from lykke.domain.entities import DayEntity
from lykke.domain.value_objects.day import Alarm, AlarmStatus


@dataclass(frozen=True)
class UpdateAlarmStatusCommand(Command):
    """Command to update an alarm's status on a day."""

    date: date
    alarm_id: UUID
    status: AlarmStatus
    snoozed_until: datetime | None = None


class UpdateAlarmStatusHandler(BaseCommandHandler[UpdateAlarmStatusCommand, Alarm]):
    """Updates an alarm's status on a day."""

    async def handle(self, command: UpdateAlarmStatusCommand) -> Alarm:
        """Update an alarm's status on a day.

        Args:
            command: The command containing the date, alarm ID, and status

        Returns:
            The updated Alarm value object

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(command.date, self.user.id)
            day = await uow.day_ro_repo.get(day_id)

            updated_alarm = day.update_alarm_status(
                command.alarm_id,
                command.status,
                snoozed_until=ensure_utc(command.snoozed_until),
            )

            if day.has_events():
                uow.add(day)
            return updated_alarm
