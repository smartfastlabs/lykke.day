"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import Depends, Request, WebSocket
from redis import asyncio as aioredis  # type: ignore

from lykke.application.commands import (
    CreateAdhocTaskHandler,
    RecordRoutineActionHandler,
    RecordTaskActionHandler,
    RescheduleDayHandler,
    ScheduleDayHandler,
    UpdateDayHandler,
)
from lykke.application.commands.day import (
    AddBrainDumpItemToDayHandler,
    AddReminderToDayHandler,
    AddRoutineToDayHandler,
    RemoveBrainDumpItemHandler,
    RemoveReminderHandler,
    UpdateBrainDumpItemStatusHandler,
    UpdateReminderStatusHandler,
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
from lykke.presentation.handler_factory import CommandHandlerFactory, QueryHandlerFactory
from lykke.presentation.api.routers.dependencies.user import (
    get_current_user,
    get_current_user_from_token,
)


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


# Query Handler Dependencies
# For HTTP routes - use get_current_user
def day_context_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetDayContextHandler:
    """Get a GetDayContextHandler instance for HTTP handlers."""
    factory = QueryHandlerFactory(user_id=user.id, ro_repo_factory=ro_repo_factory)
    return factory.create(GetDayContextHandler)


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


def preview_day_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> PreviewDayHandler:
    """Get a PreviewDayHandler instance for HTTP handlers."""
    factory = QueryHandlerFactory(user_id=user.id, ro_repo_factory=ro_repo_factory)
    return factory.create(PreviewDayHandler)


async def preview_day_handler_websocket(
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> PreviewDayHandler:
    """Get a PreviewDayHandler instance for WebSocket handlers."""
    factory = QueryHandlerFactory(user_id=user.id, ro_repo_factory=ro_repo_factory)
    return factory.create(PreviewDayHandler)


def incremental_changes_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetIncrementalChangesHandler:
    """Get a GetIncrementalChangesHandler instance for HTTP handlers."""
    factory = QueryHandlerFactory(user_id=user.id, ro_repo_factory=ro_repo_factory)
    return factory.create(GetIncrementalChangesHandler)


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


# Command Handler Dependencies
# For HTTP routes - use get_current_user
def get_reschedule_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> RescheduleDayHandler:
    """Get a RescheduleDayHandler instance for HTTP handlers."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(RescheduleDayHandler)


def get_update_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateDayHandler:
    """Get an UpdateDayHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(UpdateDayHandler)


def get_record_task_action_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> RecordTaskActionHandler:
    """Get a RecordTaskActionHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(RecordTaskActionHandler)


def get_create_adhoc_task_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateAdhocTaskHandler:
    """Get a CreateAdhocTaskHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(CreateAdhocTaskHandler)


def get_record_routine_action_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> RecordRoutineActionHandler:
    """Get a RecordRoutineActionHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(RecordRoutineActionHandler)


def get_add_reminder_to_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> AddReminderToDayHandler:
    """Get an AddReminderToDayHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(AddReminderToDayHandler)


def get_add_routine_to_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> AddRoutineToDayHandler:
    """Get an AddRoutineToDayHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(AddRoutineToDayHandler)


def get_update_reminder_status_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateReminderStatusHandler:
    """Get an UpdateReminderStatusHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(UpdateReminderStatusHandler)


def get_remove_reminder_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> RemoveReminderHandler:
    """Get a RemoveReminderHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(RemoveReminderHandler)


def get_add_brain_dump_item_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> AddBrainDumpItemToDayHandler:
    """Get an AddBrainDumpItemToDayHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(AddBrainDumpItemToDayHandler)


def get_update_brain_dump_item_status_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateBrainDumpItemStatusHandler:
    """Get an UpdateBrainDumpItemStatusHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(UpdateBrainDumpItemStatusHandler)


def get_remove_brain_dump_item_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> RemoveBrainDumpItemHandler:
    """Get a RemoveBrainDumpItemHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
    return factory.create(RemoveBrainDumpItemHandler)
