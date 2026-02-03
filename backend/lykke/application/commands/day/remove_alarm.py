"""Command to remove an alarm from a day."""

from dataclasses import dataclass
from datetime import date, time as dt_time

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class RemoveAlarmFromDayCommand(Command):
    """Command to remove an alarm from a day."""

    date: date
    name: str
    time: dt_time
    alarm_type: value_objects.AlarmType | None = None
    url: str | None = None


class RemoveAlarmFromDayHandler(
    BaseCommandHandler[RemoveAlarmFromDayCommand, value_objects.Alarm]
):
    """Removes an alarm from a day."""

    async def handle(
        self, command: RemoveAlarmFromDayCommand
    ) -> value_objects.Alarm:
        """Remove an alarm from a day.

        Args:
            command: The command containing the date and alarm details

        Returns:
            The removed Alarm value object

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(command.date, self.user.id)
            day = await uow.day_ro_repo.get(day_id)

            # Remove the alarm (this emits a domain event)
            removed_alarm = day.remove_alarm(
                command.name,
                command.time,
                alarm_type=command.alarm_type,
                url=command.url,
            )

            # Add entity to UoW for saving
            uow.add(day)
            return removed_alarm
