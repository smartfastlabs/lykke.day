"""PushSubscription query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.push_subscription import ListPushSubscriptionsHandler
from planned.application.unit_of_work import UnitOfWorkFactory

from ..services import get_unit_of_work_factory


def get_list_push_subscriptions_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListPushSubscriptionsHandler:
    """Get a ListPushSubscriptionsHandler instance."""
    return ListPushSubscriptionsHandler(uow_factory)

