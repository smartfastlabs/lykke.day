"""Generic factory functions for creating query and command handlers."""

from typing import Annotated, Callable, TypeVar, Type

from fastapi import Depends
from lykke.application.queries.base import BaseQueryHandler
from lykke.application.commands.base import BaseCommandHandler
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity

from .services import get_read_only_repository_factory, get_unit_of_work_factory
from .user import get_current_user

# Type variables for handler types
QueryHandlerT = TypeVar("QueryHandlerT", bound=BaseQueryHandler)
CommandHandlerT = TypeVar("CommandHandlerT", bound=BaseCommandHandler)


def create_query_handler(
    handler_class: Type[QueryHandlerT],
    user: UserEntity,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> QueryHandlerT:
    """Create a query handler instance with injected dependencies.

    Args:
        handler_class: The query handler class to instantiate
        user: The current user entity
        ro_repo_factory: Read-only repository factory

    Returns:
        An instance of the query handler class
    """
    ro_repos = ro_repo_factory.create(user.id)
    return handler_class(ro_repos, user.id)


def create_command_handler(
    handler_class: Type[CommandHandlerT],
    user: UserEntity,
    uow_factory: UnitOfWorkFactory,
    ro_repo_factory: ReadOnlyRepositoryFactory,
) -> CommandHandlerT:
    """Create a command handler instance with injected dependencies.

    Args:
        handler_class: The command handler class to instantiate
        user: The current user entity
        uow_factory: Unit of work factory
        ro_repo_factory: Read-only repository factory

    Returns:
        An instance of the command handler class
    """
    ro_repos = ro_repo_factory.create(user.id)
    return handler_class(ro_repos, uow_factory, user.id)


def get_query_handler(
    handler_class: Type[QueryHandlerT],
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
    def _get_handler(
        user: Annotated[UserEntity, Depends(get_current_user)],
        ro_repo_factory: Annotated[
            ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
        ],
    ) -> QueryHandlerT:
        return create_query_handler(handler_class, user, ro_repo_factory)

    return _get_handler


def get_command_handler(
    handler_class: Type[CommandHandlerT],
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
    def _get_handler(
        uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
        ro_repo_factory: Annotated[
            ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
        ],
        user: Annotated[UserEntity, Depends(get_current_user)],
    ) -> CommandHandlerT:
        return create_command_handler(handler_class, user, uow_factory, ro_repo_factory)

    return _get_handler


