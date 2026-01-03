"""PushSubscription command handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.commands.push_subscription import (
    CreatePushSubscriptionHandler,
    DeletePushSubscriptionHandler,
)
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_create_push_subscription_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreatePushSubscriptionHandler:
    """Get a CreatePushSubscriptionHandler instance."""
    return CreatePushSubscriptionHandler(uow_factory)


def get_delete_push_subscription_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DeletePushSubscriptionHandler:
    """Get a DeletePushSubscriptionHandler instance."""
    return DeletePushSubscriptionHandler(uow_factory)

