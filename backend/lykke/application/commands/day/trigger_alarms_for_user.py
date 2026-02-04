"""Command to evaluate and trigger due day alarms for the handler's user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as dt_date, datetime as dt_datetime, timedelta as dt_timedelta

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import DayRepositoryReadOnlyProtocol
from lykke.core.exceptions import NotFoundError
from lykke.core.utils.dates import get_current_date, get_current_datetime
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class TriggerAlarmsForUserCommand(Command):
    """Command to evaluate and trigger due alarms for the handler's user.

    Optional overrides for testing; when None, current date/datetime are used.
    """

    evaluation_datetime: dt_datetime | None = None
    target_date: dt_date | None = None


class TriggerAlarmsForUserHandler(
    BaseCommandHandler[TriggerAlarmsForUserCommand, None]
):
    """Evaluates day alarms for the user and marks due ones as triggered."""

    day_ro_repo: DayRepositoryReadOnlyProtocol

    async def handle(self, command: TriggerAlarmsForUserCommand) -> None:
        """Evaluate alarms for today and yesterday (snoozed only) and persist changes."""
        user = self.user
        timezone = user.settings.timezone if user.settings else None

        evaluation_time = (
            command.evaluation_datetime
            if command.evaluation_datetime is not None
            else get_current_datetime()
        )
        target_date = (
            command.target_date
            if command.target_date is not None
            else get_current_date(timezone)
        )
        previous_date = target_date - dt_timedelta(days=1)

        async with self.new_uow() as uow:
            for day_date, snoozed_only in (
                (target_date, False),
                (previous_date, True),
            ):
                try:
                    day_id = DayEntity.id_from_date_and_user(day_date, user.id)
                    day = await self.day_ro_repo.get(day_id)
                except NotFoundError as exc:
                    logger.debug(
                        f"No day found for user {user.id} on {day_date} ({exc})",
                    )
                    continue

                if not day.alarms:
                    continue

                self._evaluate_day_alarms(
                    day,
                    evaluation_time=evaluation_time,
                    snoozed_only=snoozed_only,
                )

                if day.has_events():
                    uow.add(day)

    @staticmethod
    def _evaluate_day_alarms(
        day: DayEntity,
        *,
        evaluation_time: dt_datetime,
        snoozed_only: bool,
    ) -> None:
        for alarm in day.alarms:
            if alarm.status in (
                value_objects.AlarmStatus.CANCELLED,
                value_objects.AlarmStatus.TRIGGERED,
            ):
                continue
            if alarm.status == value_objects.AlarmStatus.SNOOZED:
                if (
                    alarm.snoozed_until is None
                    or alarm.snoozed_until > evaluation_time
                ):
                    continue
            elif snoozed_only:
                continue
            if alarm.datetime is None or alarm.datetime > evaluation_time:
                continue
            day.update_alarm_status(
                alarm.id,
                value_objects.AlarmStatus.TRIGGERED,
            )
