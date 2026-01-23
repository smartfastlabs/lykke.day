"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request, WebSocket

from lykke.application.commands import ScheduleDayHandler
from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.application.queries import GetDayContextHandler, GetIncrementalChangesHandler
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)
from lykke.presentation.handler_factory import CommandHandlerFactory, QueryHandlerFactory
from lykke.presentation.api.routers.dependencies.user import get_current_user_from_token


async def get_pubsub_gateway(
    websocket: WebSocket,
) -> AsyncIterator[PubSubGatewayProtocol]:
    """Get a PubSubGateway instance using the shared Redis connection pool.

    Uses the shared Redis connection pool from app.state. The gateway uses
    the shared pool, so closing it only closes the client connection, not
    the pool itself. This maintains compatibility with FastAPI's dependency
    injection pattern.

    Args:
        websocket: FastAPI WebSocket object to access app state
    """
    # Get the shared Redis connection pool from app state
    # If None (e.g., in tests), gateway will create its own connection
    redis_pool = getattr(websocket.app.state, "redis_pool", None)

    # Create gateway with shared pool if available, otherwise create new connection
    gateway = RedisPubSubGateway(redis_pool=redis_pool)
    try:
        yield gateway
    finally:
        # Close the gateway (only closes client connection, not the shared pool)
        await gateway.close()


async def get_unit_of_work_factory(
    request: Request,
) -> AsyncIterator[UnitOfWorkFactory]:
    """Get a UnitOfWorkFactory instance for HTTP requests.

    Creates a RedisPubSubGateway with proper cleanup to avoid connection leaks.

    Args:
        request: FastAPI Request object

    Yields:
        UnitOfWorkFactory instance
    """
    redis_pool = getattr(request.app.state, "redis_pool", None)
    pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
    try:
        yield SqlAlchemyUnitOfWorkFactory(pubsub_gateway=pubsub_gateway)
    finally:
        await pubsub_gateway.close()


async def get_unit_of_work_factory_websocket(
    websocket: WebSocket,
) -> AsyncIterator[UnitOfWorkFactory]:
    """Get a UnitOfWorkFactory instance for WebSocket requests.

    Creates a RedisPubSubGateway with proper cleanup to avoid connection leaks.

    Args:
        websocket: FastAPI WebSocket object

    Yields:
        UnitOfWorkFactory instance
    """
    redis_pool = getattr(websocket.app.state, "redis_pool", None)
    pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
    try:
        yield SqlAlchemyUnitOfWorkFactory(pubsub_gateway=pubsub_gateway)
    finally:
        await pubsub_gateway.close()


def get_read_only_repository_factory() -> ReadOnlyRepositoryFactory:
    """Get a ReadOnlyRepositoryFactory instance."""
    return SqlAlchemyReadOnlyRepositoryFactory()


# For WebSocket routes - use get_current_user_from_token
async def day_context_handler_websocket(
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetDayContextHandler:
    """Get a GetDayContextHandler instance for WebSocket handlers."""
    factory = QueryHandlerFactory(user_id=user.id, ro_repo_factory=ro_repo_factory)
    return factory.create(GetDayContextHandler)


async def incremental_changes_handler_websocket(
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetIncrementalChangesHandler:
    """Get a GetIncrementalChangesHandler instance for WebSocket handlers."""
    factory = QueryHandlerFactory(user_id=user.id, ro_repo_factory=ro_repo_factory)
    return factory.create(GetIncrementalChangesHandler)


async def get_schedule_day_handler_websocket(
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
    uow_factory: Annotated[
        UnitOfWorkFactory, Depends(get_unit_of_work_factory_websocket)
    ],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> ScheduleDayHandler:
    """Get a ScheduleDayHandler instance for WebSocket handlers."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(ScheduleDayHandler)
