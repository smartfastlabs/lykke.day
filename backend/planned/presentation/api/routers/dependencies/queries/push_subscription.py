"""PushSubscription query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.push_subscription import SearchPushSubscriptionsHandler
from planned.application.unit_of_work import ReadOnlyRepositoryFactory
from planned.domain.entities import UserEntity

from ..services import get_read_only_repository_factory
from ..user import get_current_user


def get_list_push_subscriptions_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> SearchPushSubscriptionsHandler:
    """Get a SearchPushSubscriptionsHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return SearchPushSubscriptionsHandler(ro_repos, user.id)

