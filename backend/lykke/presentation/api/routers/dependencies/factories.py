"""Factory dependencies for command/query handlers."""

from typing import Annotated, Any

from fastapi import Depends

from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .services import (
    get_read_only_repository_factory,
    get_unit_of_work_factory,
    get_unit_of_work_factory_websocket,
)
from .user import get_current_user, get_current_user_from_token


def create_query_handler(handler_class: type) -> Any:
    """Dependency factory that returns a ready-to-use query handler.

    Usage: handler: Annotated[MyHandler, Depends(create_query_handler(MyHandler))]
    """

    def _dependency(
        user: Annotated[UserEntity, Depends(get_current_user)],
        ro_repo_factory: Annotated[
            ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
        ],
    ) -> Any:
        factory = QueryHandlerFactory(user=user, ro_repo_factory=ro_repo_factory)
        return factory.create(handler_class)

    return _dependency


def create_command_handler(handler_class: type) -> Any:
    """Dependency factory that returns a ready-to-use command handler.

    Usage: handler: Annotated[MyHandler, Depends(create_command_handler(MyHandler))]
    """

    def _dependency(
        user: Annotated[UserEntity, Depends(get_current_user)],
        ro_repo_factory: Annotated[
            ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
        ],
        uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ) -> Any:
        factory = CommandHandlerFactory(
            user=user,
            ro_repo_factory=ro_repo_factory,
            uow_factory=uow_factory,
        )
        return factory.create(handler_class)

    return _dependency


def create_query_handler_websocket(handler_class: type) -> Any:
    """Dependency factory that returns a ready-to-use query handler for WebSocket routes.

    Usage: handler: Annotated[MyHandler, Depends(create_query_handler_websocket(MyHandler))]
    """

    def _dependency(
        user: Annotated[UserEntity, Depends(get_current_user_from_token)],
        ro_repo_factory: Annotated[
            ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
        ],
    ) -> Any:
        factory = QueryHandlerFactory(user=user, ro_repo_factory=ro_repo_factory)
        return factory.create(handler_class)

    return _dependency


def create_command_handler_websocket(handler_class: type) -> Any:
    """Dependency factory that returns a ready-to-use command handler for WebSocket routes.

    Usage: handler: Annotated[MyHandler, Depends(create_command_handler_websocket(MyHandler))]
    """

    def _dependency(
        user: Annotated[UserEntity, Depends(get_current_user_from_token)],
        ro_repo_factory: Annotated[
            ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
        ],
        uow_factory: Annotated[
            UnitOfWorkFactory, Depends(get_unit_of_work_factory_websocket)
        ],
    ) -> Any:
        factory = CommandHandlerFactory(
            user=user,
            ro_repo_factory=ro_repo_factory,
            uow_factory=uow_factory,
        )
        return factory.create(handler_class)

    return _dependency


def query_handler_factory(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> QueryHandlerFactory:
    """Create a QueryHandlerFactory for HTTP routes."""
    return QueryHandlerFactory(user=user, ro_repo_factory=ro_repo_factory)


def query_handler_factory_websocket(
    user: Annotated[UserEntity, Depends(get_current_user_from_token)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> QueryHandlerFactory:
    """Create a QueryHandlerFactory for WebSocket routes."""
    return QueryHandlerFactory(user=user, ro_repo_factory=ro_repo_factory)


def command_handler_factory(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CommandHandlerFactory:
    """Create a CommandHandlerFactory for HTTP routes."""
    return CommandHandlerFactory(
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )


def command_handler_factory_websocket(
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
        user=user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
    )
