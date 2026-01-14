"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands import (
    RecordTaskActionHandler,
    ScheduleDayHandler,
    UpdateDayHandler,
)
from lykke.application.gateways.pubsub_protocol import PubSubGatewayProtocol
from lykke.application.queries import GetDayContextHandler, PreviewDayHandler
from lykke.application.unit_of_work import (
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
)
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)

from ..user import get_current_user


def get_unit_of_work_factory() -> UnitOfWorkFactory:
    """Get a UnitOfWorkFactory instance."""
    return SqlAlchemyUnitOfWorkFactory()


def get_pubsub_gateway() -> PubSubGatewayProtocol:
    """Get a PubSubGateway instance."""
    return RedisPubSubGateway()


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
