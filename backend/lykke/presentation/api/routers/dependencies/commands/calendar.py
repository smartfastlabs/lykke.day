"""Calendar command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands.calendar import (
    ResyncCalendarHandler,
    ResetCalendarDataHandler,
    SubscribeCalendarHandler,
    UnsubscribeCalendarHandler,
)
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways.google import GoogleCalendarGateway

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_google_calendar_gateway() -> GoogleCalendarGatewayProtocol:
    """Get an instance of GoogleCalendarGateway."""
    return GoogleCalendarGateway()


def get_subscribe_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    google_gateway: Annotated[
        GoogleCalendarGatewayProtocol, Depends(get_google_calendar_gateway)
    ],
) -> SubscribeCalendarHandler:
    """Get a SubscribeCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return SubscribeCalendarHandler(ro_repos, uow_factory, user.id, google_gateway)


def get_unsubscribe_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    google_gateway: Annotated[
        GoogleCalendarGatewayProtocol, Depends(get_google_calendar_gateway)
    ],
) -> UnsubscribeCalendarHandler:
    """Get an UnsubscribeCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return UnsubscribeCalendarHandler(ro_repos, uow_factory, user.id, google_gateway)


def get_resync_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    google_gateway: Annotated[
        GoogleCalendarGatewayProtocol, Depends(get_google_calendar_gateway)
    ],
) -> ResyncCalendarHandler:
    """Get a ResyncCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return ResyncCalendarHandler(ro_repos, uow_factory, user.id, google_gateway)


def get_reset_calendar_data_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    google_gateway: Annotated[
        GoogleCalendarGatewayProtocol, Depends(get_google_calendar_gateway)
    ],
) -> ResetCalendarDataHandler:
    """Get a ResetCalendarDataHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return ResetCalendarDataHandler(ro_repos, uow_factory, user.id, google_gateway)
