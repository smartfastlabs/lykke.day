"""Timing-status background worker tasks."""

from typing import Annotated, Protocol
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.commands.timing_status import EvaluateTimingStatusCommand
from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_evaluate_timing_status_handler,
    get_identity_access,
    get_read_only_repository_factory,
    get_unit_of_work_factory,
    load_user,
)


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None: ...


class _TimingStatusHandler(Protocol):
    async def handle(self, command: EvaluateTimingStatusCommand) -> None: ...


@broker.task(schedule=[{"cron": "* * * * *"}])  # type: ignore[untyped-decorator]
async def evaluate_timing_status_for_all_users_task(
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Evaluate timing status for all users every minute."""
    logger.info("Starting timing-status evaluation for all users")

    users = await identity_access.list_all_users()
    logger.info(f"Found {len(users)} users for timing-status evaluation")

    task = enqueue_task or evaluate_timing_status_for_user_task
    for user in users:
        await task.kiq(user_id=user.id)

    logger.info(f"Enqueued timing-status evaluation tasks for {len(users)} users")


@broker.task  # type: ignore[untyped-decorator]
async def evaluate_timing_status_for_user_task(
    user_id: UUID,
    *,
    handler: _TimingStatusHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Evaluate and emit timing-status changes for a specific user."""
    logger.info(f"Starting timing-status evaluation for user {user_id}")

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        resolved_handler: _TimingStatusHandler
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for timing-status task {user_id}")
                return
            resolved_handler = get_evaluate_timing_status_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        else:
            resolved_handler = handler

        try:
            await resolved_handler.handle(EvaluateTimingStatusCommand())
            logger.debug(f"Timing-status evaluation completed for user {user_id}")
        except Exception:  # pylint: disable=broad-except
            logger.exception(f"Error evaluating timing status for user {user_id}")
    finally:
        await pubsub_gateway.close()
