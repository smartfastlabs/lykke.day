"""Alarm-related background worker tasks."""

from collections.abc import Callable
from datetime import date as dt_date, datetime as dt_datetime, timedelta as dt_timedelta
from typing import Annotated, Protocol
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.repositories import UserRepositoryReadOnlyProtocol
from lykke.application.unit_of_work import UnitOfWorkFactory
from lykke.core.utils.dates import get_current_date, get_current_datetime
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import get_unit_of_work_factory, get_user_repository


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None:
        ...


@broker.task(schedule=[{"cron": "* * * * *"}])  # type: ignore[untyped-decorator]
async def trigger_alarms_for_all_users_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Trigger alarms for all users every minute."""
    logger.info("Starting alarm trigger evaluation for all users")

    users = await user_repo.all()
    logger.info(f"Found {len(users)} users to evaluate alarms")

    task = enqueue_task or trigger_alarms_for_user_task
    for user in users:
        await task.kiq(user_id=user.id)

    logger.info("Enqueued alarm trigger tasks for all users")


@broker.task  # type: ignore[untyped-decorator]
async def trigger_alarms_for_user_task(
    user_id: UUID,
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
    *,
    uow_factory: UnitOfWorkFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
    current_date_provider: Callable[[str | None], dt_date] | None = None,
    current_datetime_provider: Callable[[], dt_datetime] | None = None,
) -> None:
    """Trigger alarms for a specific user."""
    logger.info(f"Evaluating alarms for user {user_id}")

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        uow_factory = uow_factory or get_unit_of_work_factory(pubsub_gateway)

        try:
            user = await user_repo.get(user_id)
            timezone = user.settings.timezone if user.settings else None
        except Exception:
            timezone = None

        current_date_provider = current_date_provider or get_current_date
        current_datetime_provider = current_datetime_provider or get_current_datetime
        target_date = current_date_provider(timezone)
        now = current_datetime_provider()
        evaluation_time = now.replace(second=0, microsecond=0)
        previous_date = target_date - dt_timedelta(days=1)

        def evaluate_day_alarms(
            day: DayEntity,
            *,
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

        async with uow_factory.create(user_id) as uow:
            for day_date, snoozed_only in (
                (target_date, False),
                (previous_date, True),
            ):
                try:
                    day_id = DayEntity.id_from_date_and_user(day_date, user_id)
                    day = await uow.day_ro_repo.get(day_id)
                except Exception as exc:
                    logger.debug(
                        "No day found for user %s on %s (%s)",
                        user_id,
                        day_date,
                        exc,
                    )
                    continue

                if not day.alarms:
                    continue

                evaluate_day_alarms(day, snoozed_only=snoozed_only)

                if day.has_events():
                    uow.add(day)

        logger.info("Alarm evaluation completed for user %s", user_id)
    finally:
        await pubsub_gateway.close()
