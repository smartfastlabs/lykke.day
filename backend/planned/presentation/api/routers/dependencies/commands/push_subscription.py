"""PushSubscription command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.push_subscription import (
    CreatePushSubscriptionHandler,
    DeletePushSubscriptionHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import UserEntity

from ..services import get_unit_of_work_factory
from ..user import get_current_user


def get_create_push_subscription_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> CreatePushSubscriptionHandler:
    """Get a CreatePushSubscriptionHandler instance."""
    return CreatePushSubscriptionHandler(uow_factory, user.id)


def get_delete_push_subscription_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> DeletePushSubscriptionHandler:
    """Get a DeletePushSubscriptionHandler instance."""
    return DeletePushSubscriptionHandler(uow_factory, user.id)

