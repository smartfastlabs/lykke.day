"""Task query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.task import SearchTasksHandler
from planned.application.unit_of_work import ReadOnlyRepositoryFactory
from planned.domain.entities import UserEntity

from ..services import get_read_only_repository_factory
from ..user import get_current_user


def get_list_tasks_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> SearchTasksHandler:
    """Get a SearchTasksHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return SearchTasksHandler(ro_repos, user.id)

