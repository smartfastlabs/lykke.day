"""Command to add an alarm to a day."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time as dt_time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class AddAlarmToDayCommand(Command):
    """Command to add an alarm to a day."""

    date: date
    name: str | None
    time: dt_time
    alarm_type: value_objects.AlarmType = value_objects.AlarmType.URL
    url: str = ""


class AddAlarmToDayHandler(BaseCommandHandler[AddAlarmToDayCommand, value_objects.Alarm]):
    """Adds an alarm to a day."""

    @staticmethod
    def _default_alarm_name(alarm_time: dt_time) -> str:
        hour = alarm_time.hour % 12 or 12
        minute = alarm_time.minute
        period = "am" if alarm_time.hour < 12 else "pm"
        return f"{hour}:{minute:02d} {period} Alarm"

    async def handle(self, command: AddAlarmToDayCommand) -> value_objects.Alarm:
        """Add an alarm to a day.

        Args:
            command: The command containing the date and alarm details

        Returns:
            The created Alarm value object

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(command.date, self.user.id)
            day = await uow.day_ro_repo.get(day_id)

            timezone = ZoneInfo("UTC")
            try:
                user = self.user
            except NotFoundError:
                user = None
            if user and user.settings.timezone:
                try:
                    timezone = ZoneInfo(user.settings.timezone)
                except (ZoneInfoNotFoundError, ValueError):
                    timezone = ZoneInfo("UTC")

            alarm_local_dt = datetime.combine(command.date, command.time, tzinfo=timezone)
            name = (command.name or "").strip()
            if not name:
                name = self._default_alarm_name(command.time)

            alarm = value_objects.Alarm(
                name=name,
                time=command.time,
                datetime=alarm_local_dt.astimezone(UTC),
                type=command.alarm_type,
                url=command.url,
            )

            # Add the alarm (this emits a domain event)
            alarm = day.add_alarm(alarm)

            # Add entity to UoW for saving
            uow.add(day)
            return alarm
