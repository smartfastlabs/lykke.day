"""Day scheduling background worker tasks."""

from collections.abc import Callable
from datetime import date as dt_date
from typing import Annotated, Protocol
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.commands import ScheduleDayCommand
from lykke.application.repositories import UserRepositoryReadOnlyProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.core.utils.dates import get_current_date
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_read_only_repository_factory,
    get_schedule_day_handler,
    get_unit_of_work_factory,
    get_user_repository,
    load_user,
)


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None: ...


class _ScheduleDayHandler(Protocol):
    async def handle(self, command: ScheduleDayCommand) -> None: ...


@broker.task(schedule=[{"cron": "0 3 * * *"}])  # type: ignore[untyped-decorator]
async def schedule_all_users_day_task(
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Load all users and enqueue daily scheduling tasks for each user."""
    logger.info("Starting daily schedule task for all users")

    users = await user_repo.all()
    logger.info(f"Found {len(users)} users to schedule")

    task = enqueue_task or schedule_user_day_task
    for user in users:
        # Enqueue a sub-task for each user
        await task.kiq(user_id=user.id)

    logger.info(f"Enqueued daily scheduling tasks for {len(users)} users")


@broker.task  # type: ignore[untyped-decorator]
async def schedule_user_day_task(
    user_id: UUID,
    user_repo: Annotated[UserRepositoryReadOnlyProtocol, Depends(get_user_repository)],
    *,
    handler: _ScheduleDayHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
    current_date_provider: Callable[[str | None], dt_date] | None = None,
) -> None:
    """Schedule today's day for a specific user."""
    logger.info(f"Starting daily scheduling for user {user_id}")

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        try:
            user = await load_user(user_id)
        except Exception:
            logger.warning(f"User not found for scheduling task {user_id}")
            return

        schedule_handler = handler or get_schedule_day_handler(
            user=user,
            uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
        )

        timezone = user.settings.timezone if user.settings else None

        # Use user's timezone for "today"
        current_date_provider = current_date_provider or get_current_date
        target_date = current_date_provider(timezone)
        try:
            await schedule_handler.handle(ScheduleDayCommand(date=target_date))
            logger.debug(f"Scheduled {target_date} for user {user_id}")
        except ValueError as e:
            # Day template might be missing - log and continue
            logger.warning(f"Could not schedule {target_date} for user {user_id}: {e}")
        except Exception:  # pylint: disable=broad-except
            # Catch-all for resilient background job - continue with other users
            logger.exception(f"Error scheduling {target_date} for user {user_id}")

        logger.info(f"Daily scheduling completed for user {user_id}")
    finally:
        await pubsub_gateway.close()
