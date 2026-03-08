"""Scheduled tasks for LLM status check-in use cases (todays_status, this_weeks_status, this_month_status)."""

from typing import Annotated, Protocol
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.commands.user_check_in import (
    ThisMonthsStatusCommand,
    ThisWeeksStatusCommand,
    TodaysStatusCommand,
)
from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_identity_access,
    get_read_only_repository_factory,
    get_this_months_status_handler,
    get_this_weeks_status_handler,
    get_todays_status_handler,
    get_unit_of_work_factory,
    load_user,
)


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None: ...


class _TodaysStatusHandler(Protocol):
    user: UserEntity

    async def handle(self, command: TodaysStatusCommand) -> None: ...


class _ThisWeeksStatusHandler(Protocol):
    user: UserEntity

    async def handle(self, command: ThisWeeksStatusCommand) -> None: ...


class _ThisMonthsStatusHandler(Protocol):
    user: UserEntity

    async def handle(self, command: ThisMonthsStatusCommand) -> None: ...


@broker.task(schedule=[{"cron": "0 8,12,18 * * *"}])  # type: ignore[untyped-decorator]
async def run_todays_status_for_all_users_task(
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Enqueue todays_status LLM check-in for all users with LLM configured.

    Runs at 08:00, 12:00, and 18:00 UTC. Each user gets a per-user task.
    """
    logger.info("Starting todays_status check-in run for all users")
    users = await identity_access.list_all_users()
    users_with_llm = [
        u for u in users if u.settings and u.settings.llm_provider
    ]
    logger.info(f"Found {len(users_with_llm)} users with LLM provider configured")
    task = enqueue_task or run_todays_status_task
    for user in users_with_llm:
        await task.kiq(user_id=user.id)
    logger.info(f"Enqueued todays_status for {len(users_with_llm)} users")


@broker.task  # type: ignore[untyped-decorator]
async def run_todays_status_task(
    user_id: UUID,
    *,
    handler: _TodaysStatusHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Run todays_status LLM use case for one user and persist check-in."""
    logger.info(f"Starting todays_status for user {user_id}")
    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for todays_status task {user_id}")
                return
            handler = get_todays_status_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        await handler.handle(TodaysStatusCommand())
        logger.debug(f"todays_status completed for user {user_id}")
    except Exception:  # pylint: disable=broad-except
        logger.exception(f"Error running todays_status for user {user_id}")
    finally:
        await pubsub_gateway.close()


@broker.task(schedule=[{"cron": "0 9 * * 1,4"}])  # type: ignore[untyped-decorator]
async def run_this_weeks_status_for_all_users_task(
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Enqueue this_weeks_status for all users with LLM. Runs Mon and Thu 09:00 UTC."""
    logger.info("Starting this_weeks_status check-in run for all users")
    users = await identity_access.list_all_users()
    users_with_llm = [
        u for u in users if u.settings and u.settings.llm_provider
    ]
    task = enqueue_task or run_this_weeks_status_task
    for user in users_with_llm:
        await task.kiq(user_id=user.id)
    logger.info(f"Enqueued this_weeks_status for {len(users_with_llm)} users")


@broker.task  # type: ignore[untyped-decorator]
async def run_this_weeks_status_task(
    user_id: UUID,
    *,
    handler: _ThisWeeksStatusHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Run this_weeks_status LLM use case for one user."""
    logger.info(f"Starting this_weeks_status for user {user_id}")
    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for this_weeks_status task {user_id}")
                return
            handler = get_this_weeks_status_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        await handler.handle(ThisWeeksStatusCommand())
    except Exception:  # pylint: disable=broad-except
        logger.exception(f"Error running this_weeks_status for user {user_id}")
    finally:
        await pubsub_gateway.close()


@broker.task(schedule=[{"cron": "0 10 1 * *"}])  # type: ignore[untyped-decorator]
async def run_this_month_status_for_all_users_task(
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Enqueue this_month_status for all users with LLM. Runs 1st of month 10:00 UTC."""
    logger.info("Starting this_month_status check-in run for all users")
    users = await identity_access.list_all_users()
    users_with_llm = [
        u for u in users if u.settings and u.settings.llm_provider
    ]
    task = enqueue_task or run_this_month_status_task
    for user in users_with_llm:
        await task.kiq(user_id=user.id)
    logger.info(f"Enqueued this_month_status for {len(users_with_llm)} users")


@broker.task  # type: ignore[untyped-decorator]
async def run_this_month_status_task(
    user_id: UUID,
    *,
    handler: _ThisMonthsStatusHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Run this_month_status LLM use case for one user."""
    logger.info(f"Starting this_month_status for user {user_id}")
    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for this_month_status task {user_id}")
                return
            handler = get_this_months_status_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        await handler.handle(ThisMonthsStatusCommand())
    except Exception:  # pylint: disable=broad-except
        logger.exception(f"Error running this_month_status for user {user_id}")
    finally:
        await pubsub_gateway.close()
