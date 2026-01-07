"""CalendarEntry query handler dependency injection functions."""

from typing import Annotated

from fastapi import Depends
from lykke.application.queries.calendar_entry import SearchCalendarEntriesHandler
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.domain.entities import UserEntity

from ..services import get_read_only_repository_factory
from ..user import get_current_user


def get_list_calendar_entries_handler(
    user: Annotated[UserEntity, Depends(get_current_user)],
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
    ],
) -> SearchCalendarEntriesHandler:
    """Get a SearchCalendarEntriesHandler instance."""
    ro_repos = ro_repo_factory.create(user.id)
    return SearchCalendarEntriesHandler(ro_repos, user.id)

