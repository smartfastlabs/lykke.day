"""Calendar command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands.calendar import (
    ResyncCalendarHandler,
    ResetCalendarDataHandler,
    ResetCalendarSyncHandler,
    SubscribeCalendarHandler,
    UnsubscribeCalendarHandler,
)
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways.google import GoogleCalendarGateway
from lykke.presentation.handler_factory import CommandHandlerFactory

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
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(SubscribeCalendarHandler)


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
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(UnsubscribeCalendarHandler)


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
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(ResyncCalendarHandler)


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
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(ResetCalendarDataHandler)


def get_reset_calendar_sync_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
    google_gateway: Annotated[
        GoogleCalendarGatewayProtocol, Depends(get_google_calendar_gateway)
    ],
) -> ResetCalendarSyncHandler:
    """Get a ResetCalendarSyncHandler instance."""
    factory = CommandHandlerFactory(
        user_id=user.id,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    )
    return factory.create(ResetCalendarSyncHandler)
