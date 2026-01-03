"""DayTemplate query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from planned.application.queries.day_template import (
    GetDayTemplateHandler,
    ListDayTemplatesHandler,
)
from planned.application.unit_of_work import ReadOnlyRepositoryFactory
from planned.domain.entities import UserEntity

from ..services import get_read_only_repository_factory
from ..user import get_current_user


def get_get_day_template_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetDayTemplateHandler:
    """Get a GetDayTemplateHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return GetDayTemplateHandler(ro_repos)


def get_list_day_templates_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> ListDayTemplatesHandler:
    """Get a ListDayTemplatesHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return ListDayTemplatesHandler(ro_repos)

