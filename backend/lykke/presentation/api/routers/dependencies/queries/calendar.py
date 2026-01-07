"""Calendar query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.queries.calendar import (
    GetCalendarHandler,
    SearchCalendarsHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory
from ..user import get_current_user


def get_get_calendar_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> GetCalendarHandler:
    """Get a GetCalendarHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return GetCalendarHandler(ro_repos, user.id)


def get_list_calendars_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> SearchCalendarsHandler:
    """Get a SearchCalendarsHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return SearchCalendarsHandler(ro_repos, user.id)

