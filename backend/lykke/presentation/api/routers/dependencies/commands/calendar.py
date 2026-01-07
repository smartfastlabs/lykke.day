"""Calendar command handler dependency injection functions."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from lykke.application.commands.calendar import (
    CreateCalendarHandler,
    DeleteCalendarHandler,
    RecordWebhookNotificationHandler,
    SyncCalendarChangesHandler,
    UpdateCalendarHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways.google import GoogleCalendarGateway

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_sync_calendar_changes_handler(
    user_id: Annotated[UUID, Path()],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> SyncCalendarChangesHandler:
    """Get a SyncCalendarChangesHandler instance for webhook use (user_id from path)."""
    ro_repos = ro_repo_factory.create(user_id)
    return SyncCalendarChangesHandler(
        ro_repos=ro_repos,
        uow_factory=uow_factory,
        user_id=user_id,
        google_gateway=GoogleCalendarGateway(),
    )


def get_create_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreateCalendarHandler:
    """Get a CreateCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return CreateCalendarHandler(ro_repos, uow_factory, user.id)


def get_update_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> UpdateCalendarHandler:
    """Get an UpdateCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return UpdateCalendarHandler(ro_repos, uow_factory, user.id)


def get_delete_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeleteCalendarHandler:
    """Get a DeleteCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return DeleteCalendarHandler(ro_repos, uow_factory, user.id)


def get_record_webhook_notification_handler(
    user_id: Annotated[UUID, Path()],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> RecordWebhookNotificationHandler:
    """Get a RecordWebhookNotificationHandler instance for webhook use (user_id from path)."""
    ro_repos = ro_repo_factory.create(user_id)
    return RecordWebhookNotificationHandler(
        ro_repos=ro_repos,
        uow_factory=uow_factory,
        user_id=user_id,
    )
