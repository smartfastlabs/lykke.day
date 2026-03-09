"""Scheduled tasks for the user_status_use_case LLM check-in use case."""

from typing import Annotated, Protocol
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.commands.user_check_in import (
    UserStatusUseCaseCommand,
)
from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_identity_access,
    get_read_only_repository_factory,
    get_user_status_use_case_handler,
    get_unit_of_work_factory,
    load_user,
)


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None: ...


class _UserStatusUseCaseHandler(Protocol):
    user: UserEntity

    async def handle(self, command: UserStatusUseCaseCommand) -> None: ...


@broker.task(schedule=[{"cron": "0 8,12,18 * * *"}])  # type: ignore[untyped-decorator]
async def run_user_status_use_case_for_all_users_task(
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Enqueue user_status_use_case LLM check-in for all users with LLM configured.

    Runs at 08:00, 12:00, and 18:00 UTC. Each user gets a per-user task.
    """
    logger.info("Starting user_status_use_case check-in run for all users")
    users = await identity_access.list_all_users()
    users_with_llm = [
        u for u in users if u.settings and u.settings.llm_provider
    ]
    logger.info(f"Found {len(users_with_llm)} users with LLM provider configured")
    task = enqueue_task or run_user_status_use_case_task
    for user in users_with_llm:
        await task.kiq(user_id=user.id)
    logger.info(f"Enqueued user_status_use_case for {len(users_with_llm)} users")


@broker.task  # type: ignore[untyped-decorator]
async def run_user_status_use_case_task(
    user_id: UUID,
    *,
    handler: _UserStatusUseCaseHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Run user_status_use_case LLM use case for one user and persist check-in."""
    logger.info(f"Starting user_status_use_case for user {user_id}")
    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for user_status_use_case task {user_id}")
                return
            handler = get_user_status_use_case_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )
        await handler.handle(UserStatusUseCaseCommand())
        logger.debug(f"user_status_use_case completed for user {user_id}")
    except Exception:  # pylint: disable=broad-except
        logger.exception(f"Error running user_status_use_case for user {user_id}")
    finally:
        await pubsub_gateway.close()


