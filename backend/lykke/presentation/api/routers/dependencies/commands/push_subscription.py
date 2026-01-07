"""PushSubscription command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.commands.push_subscription import (
    CreatePushSubscriptionHandler,
    DeletePushSubscriptionHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory, get_unit_of_work_factory
from ..user import get_current_user


def get_create_push_subscription_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreatePushSubscriptionHandler:
    """Get a CreatePushSubscriptionHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return CreatePushSubscriptionHandler(ro_repos, uow_factory, user.id)


def get_delete_push_subscription_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeletePushSubscriptionHandler:
    """Get a DeletePushSubscriptionHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return DeletePushSubscriptionHandler(ro_repos, uow_factory, user.id)

