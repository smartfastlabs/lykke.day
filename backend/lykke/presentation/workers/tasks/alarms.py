"""Alarm-related background worker tasks."""

from typing import Annotated, Protocol
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.commands.day import (
    TriggerAlarmsForUserCommand,
    TriggerAlarmsForUserHandler,
)
from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_read_only_repository_factory,
    get_trigger_alarms_for_user_handler,
    get_unit_of_work_factory,
    get_identity_access,
)


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None: ...


@broker.task(schedule=[{"cron": "* * * * *"}])  # type: ignore[untyped-decorator]
async def trigger_alarms_for_all_users_task(
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Trigger alarms for all users every minute."""
    logger.info("Starting alarm trigger evaluation for all users")

    users = await identity_access.list_all_users()
    logger.info(f"Found {len(users)} users to evaluate alarms")

    task = enqueue_task or trigger_alarms_for_user_task
    for user in users:
        await task.kiq(user_id=user.id)

    logger.info("Enqueued alarm trigger tasks for all users")


@broker.task  # type: ignore[untyped-decorator]
async def trigger_alarms_for_user_task(
    user_id: UUID,
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
    command: TriggerAlarmsForUserCommand | None = None,
) -> None:
    """Trigger alarms for a specific user."""
    logger.info(f"Evaluating alarms for user {user_id}")

    gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        uow_factory = uow_factory or get_unit_of_work_factory(gateway)
        ro_repo_factory = ro_repo_factory or get_read_only_repository_factory()

        user = await identity_access.get_user_by_id(user_id)
        if user is None:
            logger.warning(f"User not found for alarm evaluation {user_id}")
            return

        handler = get_trigger_alarms_for_user_handler(
            user=user,
            uow_factory=uow_factory,
            ro_repo_factory=ro_repo_factory,
        )
        await handler.handle(command or TriggerAlarmsForUserCommand())

        logger.info(f"Alarm evaluation completed for user {user_id}")
    finally:
        await gateway.close()
