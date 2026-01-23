"""Generic factory functions for creating query and command handlers."""

from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import Depends

from lykke.application.commands.base import BaseCommandHandler
from lykke.application.queries.base import BaseQueryHandler
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.presentation.handler_factory import CommandHandlerFactory, QueryHandlerFactory

from .services import (
    get_read_only_repository_factory,
    get_unit_of_work_factory,
    get_unit_of_work_factory_websocket,
)
from .user import get_current_user, get_current_user_from_token

# Type variables for handler types
QueryHandlerT = TypeVar("QueryHandlerT", bound=BaseQueryHandler)
CommandHandlerT = TypeVar("CommandHandlerT", bound=BaseCommandHandler)


def get_query_handler_factory(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> QueryHandlerFactory:
    """Create a QueryHandlerFactory for HTTP routes."""
    return QueryHandlerFactory(user_id=user.id, ro_repo_factory=ro_repo_factory)


def get_query_handler_factory_websocket(
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> QueryHandlerFactory:
    """Create a QueryHandlerFactory for WebSocket routes."""
    return QueryHandlerFactory(user_id=user.id, ro_repo_factory=ro_repo_factory)


def get_command_handler_factory(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CommandHandlerFactory:
    """Create a CommandHandlerFactory for HTTP routes."""
    return CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )


def get_command_handler_factory_websocket(
    uow_factory: Annotated[
        UnitOfWorkFactory, Depends(get_unit_of_work_factory_websocket)
    ],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
) -> CommandHandlerFactory:
    """Create a CommandHandlerFactory for WebSocket routes."""
    return CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )


def load_query_handler(
    handler_class: type[QueryHandlerT],
    *,
    factory_dependency: Callable[..., QueryHandlerFactory] = get_query_handler_factory,
) -> Callable[..., QueryHandlerT]:
    """Create a dependency function for a query handler using a factory."""

    def _get_handler(
        factory: Annotated[QueryHandlerFactory, Depends(factory_dependency)],
    ) -> QueryHandlerT:
        return factory.create(handler_class)

    return _get_handler


def load_command_handler(
    handler_class: type[CommandHandlerT],
    *,
    factory_dependency: Callable[..., CommandHandlerFactory] = get_command_handler_factory,
) -> Callable[..., CommandHandlerT]:
    """Create a dependency function for a command handler using a factory."""

    def _get_handler(
        factory: Annotated[CommandHandlerFactory, Depends(factory_dependency)],
    ) -> CommandHandlerT:
        return factory.create(handler_class)

    return _get_handler


def get_query_handler(
    handler_class: type[QueryHandlerT],
) -> Callable[..., QueryHandlerT]:
    """Create a FastAPI dependency function for a query handler.

    Usage:
        @router.get("/{id}")
        async def get_item(
            handler: Annotated[
                GetItemHandler,
                Depends(get_query_handler(GetItemHandler))
            ],
        ):
            ...

    Args:
        handler_class: The query handler class to create a dependency for

    Returns:
        A dependency function that can be used with FastAPI's Depends()
    """

    return load_query_handler(handler_class)


def get_command_handler(
    handler_class: type[CommandHandlerT],
) -> Callable[..., CommandHandlerT]:
    """Create a FastAPI dependency function for a command handler.

    Usage:
        @router.post("/")
        async def create_item(
            handler: Annotated[
                CreateItemHandler,
                Depends(get_command_handler(CreateItemHandler))
            ],
        ):
            ...

    Args:
        handler_class: The command handler class to create a dependency for

    Returns:
        A dependency function that can be used with FastAPI's Depends()
    """

    return load_command_handler(handler_class)
