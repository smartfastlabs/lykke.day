"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from redis import asyncio as aioredis  # type: ignore

from lykke.application.commands import (
    RecordTaskActionHandler,
    ScheduleDayHandler,
    UpdateDayHandler,
)
from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.application.queries import (
    GetDayContextHandler,
    GetIncrementalChangesHandler,
    PreviewDayHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)
from lykke.presentation.api.routers.dependencies.user import get_current_user


async def get_pubsub_gateway(
    request: Request,
) -> AsyncIterator[PubSubGatewayProtocol]:
    """Get a PubSubGateway instance using the shared Redis connection pool.

    Uses the shared Redis connection pool from app.state. The gateway uses
    the shared pool, so closing it only closes the client connection, not
    the pool itself. This maintains compatibility with FastAPI's dependency
    injection pattern.

    Args:
        request: FastAPI request object to access app state
    """
    # Get the shared Redis connection pool from app state
    # If None (e.g., in tests), gateway will create its own connection
    redis_pool = getattr(request.app.state, "redis_pool", None)

    # Create gateway with shared pool if available, otherwise create new connection
    gateway = RedisPubSubGateway(redis_pool=redis_pool)
    try:
        yield gateway
    finally:
        # Close the gateway (only closes client connection, not the shared pool)
        await gateway.close()


def get_unit_of_work_factory(
    pubsub_gateway: Annotated[PubSubGatewayProtocol, Depends(get_pubsub_gateway)],
) -> UnitOfWorkFactory:
    """Get a UnitOfWorkFactory instance."""
    return SqlAlchemyUnitOfWorkFactory(pubsub_gateway=pubsub_gateway)


def get_read_only_repository_factory() -> ReadOnlyRepositoryFactory:
    """Get a ReadOnlyRepositoryFactory instance."""
    return SqlAlchemyReadOnlyRepositoryFactory()


# Query Handler Dependencies
def get_get_day_context_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetDayContextHandler:
    """Get a GetDayContextHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return GetDayContextHandler(ro_repos, user.id)


def get_preview_day_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> PreviewDayHandler:
    """Get a PreviewDayHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return PreviewDayHandler(ro_repos, user.id)


def get_get_incremental_changes_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetIncrementalChangesHandler:
    """Get a GetIncrementalChangesHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return GetIncrementalChangesHandler(ro_repos, user.id)


# Command Handler Dependencies
def get_schedule_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    preview_day_handler: Annotated[PreviewDayHandler, Depends(get_preview_day_handler)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> ScheduleDayHandler:
    """Get a ScheduleDayHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return ScheduleDayHandler(ro_repos, uow_factory, user.id, preview_day_handler)


def get_update_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateDayHandler:
    """Get an UpdateDayHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return UpdateDayHandler(ro_repos, uow_factory, user.id)


def get_record_task_action_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> RecordTaskActionHandler:
    """Get a RecordTaskActionHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return RecordTaskActionHandler(ro_repos, uow_factory, user.id)
